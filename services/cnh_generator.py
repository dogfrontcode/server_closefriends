# -*- coding: utf-8 -*-
"""
🖼️ CNH Image Generator - Gerador otimizado de imagens CNH

Sistema otimizado para geração de CNHs com:
- Organização por CPF
- Paths centralizados
- Melhor tratamento de erros
- Arquitetura limpa
"""

from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime, date
import logging
from typing import Tuple, Optional, Dict, Any
import sys

# Imports locais
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from static.cnh_matriz.front_coordinates import CNH_COORDINATES, FONT_CONFIGS, TEMPLATE_PATH, FOTO_3X4_AREA, ASSINATURA_AREA
from static.cnh_matriz.back_coordinates import CNH_BACK_COORDINATES, BACK_FONT_CONFIGS, BACK_TEMPLATE_PATH, QR_CODE_AREA, CODIGOS_RESTRICAO
from services.path_manager import CNHPathManager, CNHPaths

logger = logging.getLogger(__name__)

class CNHImageGenerator:
    """
    Gerador de imagem CNH usando template oficial.
    Usa coordenadas definidas na matriz para posicionamento preciso.
    """
    
    # Configurações da imagem
    IMAGE_WIDTH = 700  # Largura do template
    IMAGE_HEIGHT = 440  # Altura do template
    TEXT_COLOR = (0, 0, 0)  # Preto para texto
    
    # Diretórios
    OUTPUT_DIR = "static/uploads/cnh"  # Nova estrutura em uploads
    FONTS_DIR = "static/fonts"
    TEMPLATE_PATH = "static/cnh_matriz/front-cnh.png"
    
    def __init__(self):
        """Inicializa gerador e garante que diretórios existem."""
        self._ensure_directories()
        self._load_fonts()
    
    def _ensure_directories(self):
        """Cria diretórios necessários se não existirem."""
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.FONTS_DIR, exist_ok=True)
    
    def _ensure_cnh_directory(self, cnh_request, file_type="front"):
        """
        DEPRECATED: Use CNHPathManager.create_cnh_paths() instead.
        Mantido para compatibilidade temporária.
        """
        logger.warning("_ensure_cnh_directory é deprecated. Use CNHPathManager.create_cnh_paths()")
        
        # Fallback para compatibilidade
        folder_mapping = {"cnh_front": "front", "cnh_back": "back", "qr_code": "qrcode", "front": "front", "back": "back", "qrcode": "qrcode"}
        folder_name = folder_mapping.get(file_type, "front")
        cpf_limpo = ''.join(filter(str.isdigit, cnh_request.cpf)) if cnh_request.cpf else f"user_{cnh_request.user_id}"
        cnh_dir = os.path.join(self.OUTPUT_DIR, cpf_limpo, folder_name)
        os.makedirs(cnh_dir, exist_ok=True)
        return cnh_dir
    
    def _load_fonts(self):
        """Carrega fontes para uso na imagem com suporte UTF-8."""
        try:
            # Usar o método melhorado para carregar fontes UTF-8
            self.title_font = self._get_font(24)
            self.header_font = self._get_font(32)
            self.data_font = self._get_font(18)
            self.small_font = self._get_font(14)
                
            logger.info("Fontes UTF-8 carregadas com sucesso")
            
        except Exception as e:
            logger.warning(f"Erro ao carregar fontes UTF-8: {e}. Usando fonte padrão.")
            # Usar fontes padrão
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.data_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
    
    def generate_basic_cnh(self, cnh_request, output_path=None):
        """
        Gera CNH usando template oficial com coordenadas precisas.
        
        Args:
            cnh_request: Objeto CNHRequest com dados
            output_path: Caminho específico para salvar (opcional)
            
        Returns:
            str: Caminho do arquivo gerado
            
        Raises:
            Exception: Se houver erro na geração
        """
        try:
            logger.info(f"Iniciando geração de CNH com template - ID: {cnh_request.id}")
            
            # Carregar template base
            template_path = os.path.join(os.path.dirname(__file__), '..', self.TEMPLATE_PATH)
            if not os.path.exists(template_path):
                logger.warning(f"Template não encontrado: {template_path}. Usando imagem em branco.")
                # Fallback: criar imagem em branco se template não existir
                image = Image.new('RGB', (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), (255, 255, 255))
            else:
                image = Image.open(template_path).copy()
            
            draw = ImageDraw.Draw(image)
            
            # Aplicar dados usando coordenadas da matriz
            try:
                self._apply_data_with_coordinates(draw, cnh_request)
                # Processar foto 3x4 se fornecida
                self._process_foto_3x4(image, cnh_request)
                # Processar assinatura se fornecida
                self._process_signature(image, cnh_request)
            except Exception as e:
                logger.error(f"Erro ao aplicar coordenadas: {str(e)}")
                # Fallback: desenhar apenas o nome no centro para testar
                draw.text((100, 200), cnh_request.nome_completo or "TESTE", fill=(0, 0, 0))
            
            # Usar path específico ou gerar automaticamente
            if output_path:
                filepath = output_path
                # Garantir que o diretório existe
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                # Criar diretório da CNH e gerar nome único para arquivo
                cnh_dir = self._ensure_cnh_directory(cnh_request, "cnh_front")
                filename = self._generate_filename(cnh_request, "cnh_front")
                filepath = os.path.join(cnh_dir, filename)
            
            # Salvar imagem da frente
            image.save(filepath, 'PNG', quality=95)
            
            logger.info(f"CNH FRENTE gerada - Arquivo: {filepath}")
            
            # TEMPORÁRIO: Gerar também o verso para teste
            try:
                back_path = self.generate_back_cnh(cnh_request)
                logger.info(f"CNH VERSO gerada - Arquivo: {back_path}")
            except Exception as e:
                logger.error(f"Erro ao gerar verso: {str(e)}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao gerar CNH - ID: {cnh_request.id}, Erro: {str(e)}")
            raise e
    
    def _apply_data_with_coordinates(self, draw, cnh_request):
        """
        Aplica os dados da CNH usando as coordenadas definidas na matriz.
        
        Args:
            draw: Objeto ImageDraw
            cnh_request: Objeto CNHRequest com dados
        """
        try:
            # Função auxiliar para desenhar campo se coordenada existir
            def draw_field_if_exists(field_name, text, rotated=False, rotation=0):
                if text and field_name in CNH_COORDINATES and field_name in FONT_CONFIGS:
                    coord = CNH_COORDINATES[field_name]
                    font_config = FONT_CONFIGS[field_name]
                    is_bold = font_config.get("bold", False)
                    font = self._get_font(font_config["size"], bold=is_bold)
                    
                    if rotated:
                        self._draw_rotated_text(draw, str(text), coord, font, font_config["color"], rotation)
                    else:
                        draw.text(coord, str(text), fill=font_config["color"], font=font)
                    logger.debug(f"Campo '{field_name}' desenhado: '{text}' em {coord}")
                    return True
                else:
                    logger.debug(f"Campo '{field_name}' ignorado - texto: '{text}', tem_coord: {field_name in CNH_COORDINATES}, tem_font: {field_name in FONT_CONFIGS}")
                return False
            
            # Nome completo
            nome_completo = cnh_request.nome_completo or ""
            draw_field_if_exists("nome_completo", nome_completo.upper())
            
            # Número da habilitação (customizado com dimensões específicas)
            numero_habilitacao = cnh_request.numero_registro or f"{cnh_request.id + 5000000000:011d}"
            self._draw_numero_habilitacao_vertical(draw, str(numero_habilitacao), (50, 304))
            
            # Outros campos - só desenha se tiver coordenadas definidas
            
            # Primeira habilitação
            if cnh_request.primeira_habilitacao:
                primeira_hab = cnh_request.primeira_habilitacao.strftime("%d/%m/%Y")
                draw_field_if_exists("primeira_habilitacao", primeira_hab)
            
            # Data, Local e UF de nascimento (concatenados)
            data_local_uf_concatenado = ""
            if cnh_request.data_nascimento:
                data_nasc = cnh_request.data_nascimento.strftime("%d/%m/%Y")
                local_nasc = cnh_request.local_nascimento or "NÃO INFORMADO"
                uf_nasc = cnh_request.uf_nascimento or "UF"
                data_local_uf_concatenado = f"{data_nasc}, {local_nasc.upper()}, {uf_nasc.upper()}"
                draw_field_if_exists("data_local_uf_nascimento", data_local_uf_concatenado)
            
            # Data de emissão
            if cnh_request.data_emissao:
                data_emissao = cnh_request.data_emissao.strftime("%d/%m/%Y")
            else:
                data_emissao = cnh_request.created_at.strftime("%d/%m/%Y")
            draw_field_if_exists("data_emissao", data_emissao)
            
            # Data de validade
            if cnh_request.validade:
                data_validade = cnh_request.validade.strftime("%d/%m/%Y")
            else:
                from datetime import timedelta
                data_validade = (cnh_request.created_at + timedelta(days=365*5)).strftime("%d/%m/%Y")
            draw_field_if_exists("validade", data_validade)
            
            # ACC
            acc = cnh_request.acc or "NAO"
            acc_text = "S" if acc == "SIM" else "N"
            draw_field_if_exists("acc", acc_text)
            
            # Categoria
            categoria = cnh_request.categoria_habilitacao or "B"
            draw_field_if_exists("categoria", categoria)
            
            # Documento de identidade
            doc_numero = cnh_request.doc_identidade_numero or ""
            doc_orgao = cnh_request.doc_identidade_orgao or "SSP"
            doc_uf = cnh_request.doc_identidade_uf or "SP"
            if doc_numero:
                doc_completo = f"{doc_numero} {doc_orgao} {doc_uf}"
                draw_field_if_exists("doc_identidade", doc_completo)
            
            # CPF
            cpf = cnh_request.cpf or ""
            draw_field_if_exists("cpf", cpf)
            
            # Número de registro
            numero_registro = cnh_request.numero_registro or f"{cnh_request.id:011d}"
            draw_field_if_exists("numero_registro", numero_registro)
            
            # Nacionalidade (sempre fixo)
            nacionalidade = "BRASILEIRO(A)"  # String fixa sempre
            draw_field_if_exists("nacionalidade", nacionalidade)
            
            # Filiação (pai e mãe em linhas separadas)
            nome_pai = cnh_request.nome_pai or ""
            nome_mae = cnh_request.nome_mae or ""
            
            # Se tem pai e mãe, desenha os dois
            if nome_pai and nome_mae:
                draw_field_if_exists("nome_pai", nome_pai.upper())  # Primeira linha
                draw_field_if_exists("nome_mae", nome_mae.upper())  # Segunda linha
            # Se só tem mãe, coloca ela na primeira linha (posição do pai)
            elif nome_mae:
                draw_field_if_exists("nome_pai", nome_mae.upper())  # Mãe na posição do pai
            # Se só tem pai (raro), coloca na primeira linha
            elif nome_pai:
                draw_field_if_exists("nome_pai", nome_pai.upper())
                
            logger.info("Dados aplicados com sucesso usando coordenadas da matriz")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar dados com coordenadas: {str(e)}")
            raise e
    
    def _get_font(self, size, bold=False):
        """
        Retorna fonte com tamanho especificado que suporte UTF-8.
        
        Args:
            size: Tamanho da fonte
            bold: Se True, usa fonte bold
            
        Returns:
            ImageFont: Objeto de fonte
        """
        # Lista de fontes que suportam UTF-8, em ordem de preferência
        if bold:
            font_candidates = [
                # Fontes ASUL Bold - prioridade
                os.path.join(self.FONTS_DIR, "ASUL-BOLD.TTF"),
                os.path.join(self.FONTS_DIR, "ASUL-REGULAR.TTF"),  # fallback
                # Fontes Google Fonts (Arvo) - fallback secundário
                os.path.join(self.FONTS_DIR, "Arvo-Bold.ttf"),
                os.path.join(self.FONTS_DIR, "Arvo-Regular.ttf"),
            ]
        else:
            font_candidates = [
                # Fontes ASUL Regular - prioridade
                os.path.join(self.FONTS_DIR, "ASUL-REGULAR.TTF"),
                os.path.join(self.FONTS_DIR, "ASUL-BOLD.TTF"),  # fallback
                # Fontes Google Fonts (Arvo) - fallback secundário
                os.path.join(self.FONTS_DIR, "Arvo-Regular.ttf"),
                os.path.join(self.FONTS_DIR, "Arvo-Bold.ttf"),
            ]
        
        # Adicionar fontes do sistema como fallback
        font_candidates.extend([
            # Fontes do macOS
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            # Fontes personalizadas
            os.path.join(self.FONTS_DIR, "arial.ttf"),
            os.path.join(self.FONTS_DIR, "DejaVuSans.ttf"),
            # Fontes do sistema Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # Fontes do Windows
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            # Tentar pelo nome
            "arial.ttf",
            "Arial",
            "DejaVu Sans",
            "Liberation Sans"
        ])
        
        for font_path in font_candidates:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    # Testar se a fonte suporta caracteres brasileiros
                    self._test_font_utf8(font)
                    return font
                else:
                    # Tentar carregar pelo nome (funciona em alguns sistemas)
                    font = ImageFont.truetype(font_path, size)
                    self._test_font_utf8(font)
                    return font
            except Exception:
                continue
                
        # Fallback para fonte padrão
        logger.warning(f"Nenhuma fonte UTF-8 encontrada para tamanho {size}. Usando fonte padrão.")
        return ImageFont.load_default()
    
    def _test_font_utf8(self, font):
        """
        Testa se a fonte suporta caracteres UTF-8 brasileiros.
        
        Args:
            font: Objeto ImageFont
            
        Raises:
            Exception: Se a fonte não suportar UTF-8
        """
        test_chars = "ÃÇáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ"
        try:
            # Criar imagem temporária para testar
            temp_img = Image.new('RGB', (100, 50), (255, 255, 255))
            temp_draw = ImageDraw.Draw(temp_img)
            temp_draw.text((10, 10), test_chars, font=font, fill=(0, 0, 0))
        except Exception as e:
            raise Exception(f"Fonte não suporta UTF-8: {e}")
    
    def _draw_rotated_text(self, draw, text, position, font, color, rotation=90):
        """
        Desenha texto rotacionado na imagem.
        
        Args:
            draw: Objeto ImageDraw
            text: Texto a ser desenhado
            position: Posição (x, y) onde desenhar
            font: Fonte do texto
            color: Cor do texto
            rotation: Ângulo de rotação em graus (90 = vertical)
        """
        try:
            # Obter dimensões do texto
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Criar imagem temporária para o texto (com muito mais margem para strings longas)
            if rotation in [90, 270]:
                # Para rotações de 90° e 270°, invertemos largura e altura
                temp_img = Image.new('RGBA', (text_height + 80, text_width + 80), (255, 255, 255, 0))
            else:
                temp_img = Image.new('RGBA', (text_width + 80, text_height + 80), (255, 255, 255, 0))
            
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Desenhar texto na imagem temporária (com mais margem)
            temp_draw.text((40, 40), text, font=font, fill=color)
            
            # Rotacionar a imagem temporária
            if rotation != 0:
                temp_img = temp_img.rotate(rotation, expand=True)
            
            # Colar a imagem rotacionada na imagem principal
            # Para texto vertical, ajustar a posição para que fique bem posicionado
            x, y = position
            if rotation == 90:
                # Texto vertical (de baixo para cima)
                paste_x = int(x - temp_img.width // 2)
                paste_y = int(y)
            elif rotation == 270:
                # Texto vertical (de cima para baixo) - ajustar para mostrar texto completo
                paste_x = int(x - temp_img.width // 2)
                paste_y = int(y - temp_img.height + 60)  # Ajuste maior para não cortar o texto
            else:
                # Texto horizontal
                paste_x = int(x)
                paste_y = int(y)
            
            # Verificar se a posição está dentro dos limites da imagem (com margem de tolerância)
            main_width, main_height = draw._image.size
            if paste_x < -20:  # Permitir que parte do texto saia da imagem se necessário
                paste_x = -20
            if paste_y < -20:
                paste_y = -20
            if paste_x + temp_img.width > main_width + 20:
                paste_x = main_width + 20 - temp_img.width
            if paste_y + temp_img.height > main_height + 20:
                paste_y = main_height + 20 - temp_img.height
            
            # Colar usando a própria imagem como máscara para transparência
            draw._image.paste(temp_img, (paste_x, paste_y), temp_img)
            
            logger.debug(f"Texto rotacionado '{text}' desenhado em ({paste_x}, {paste_y}) com rotação {rotation}°")
            
        except Exception as e:
            logger.error(f"Erro ao desenhar texto rotacionado: {str(e)}")
            # Fallback: desenhar texto normal se a rotação falhar
            draw.text(position, text, font=font, fill=color)
    
    def _draw_numero_habilitacao_custom(self, draw, numero_text, position):
        """
        Desenha o número da habilitação em uma área específica com dimensões 23x161.
        
        Args:
            draw: Objeto ImageDraw
            numero_text: Texto do número da habilitação
            position: Posição (x, y) onde desenhar
        """
        try:
            x, y = position
            area_width = 23
            area_height = 161
            
            # Configurar fonte bold
            font_config = FONT_CONFIGS.get("numero_habilitacao", {"size": 12, "bold": True})
            is_bold = font_config.get("bold", True)
            font_size = font_config.get("size", 12)
            color = font_config.get("color", (0, 0, 0))
            
            # Obter fonte bold
            font = self._get_font(font_size, bold=is_bold)
            
            # Calcular o tamanho real do texto
            bbox = draw.textbbox((0, 0), numero_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Ajustar tamanho da fonte se necessário para caber na área
            adjusted_font_size = font_size
            while text_height > area_height - 4 and adjusted_font_size > 8:
                adjusted_font_size -= 1
                font = self._get_font(adjusted_font_size, bold=is_bold)
                bbox = draw.textbbox((0, 0), numero_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            
            # Criar imagem temporária com margem extra para evitar corte
            temp_width = max(area_width, text_width + 10)
            temp_height = max(area_height, text_height + 10)
            temp_img = Image.new('RGBA', (temp_width, temp_height), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Centralizar o texto na imagem temporária
            text_x = (temp_width - text_width) // 2
            text_y = (temp_height - text_height) // 2
            temp_draw.text((text_x, text_y), numero_text, font=font, fill=color)
            
            # Rotacionar 90 graus para ficar de lado
            temp_img = temp_img.rotate(90, expand=True)
            
            # Ajustar posição para ficar dentro da área designada
            final_x = x - (temp_img.width - area_width) // 2
            final_y = y - (temp_img.height - area_height) // 2
            
            # Colar na imagem principal
            draw._image.paste(temp_img, (final_x, final_y), temp_img)
            
            logger.debug(f"Número habilitação '{numero_text}' desenhado customizado em {position} com dimensões {area_width}x{area_height}, fonte {adjusted_font_size}px")
            
        except Exception as e:
            logger.error(f"Erro ao desenhar número habilitação customizado: {str(e)}")
            # Fallback para texto normal
            font = self._get_font(12, bold=True)
            draw.text(position, numero_text, font=font, fill=(0, 0, 0))
    
    def _draw_numero_habilitacao_vertical(self, draw, numero_text, position):
        """
        Desenha o número da habilitação verticalmente na posição especificada.
        Garante que toda a string seja impressa com fonte bold.
        
        Args:
            draw: Objeto ImageDraw
            numero_text: Texto do número da habilitação
            position: Posição (x, y) onde desenhar
        """
        try:
            x, y = position
            area_width = 23
            area_height = 161
            
            # Configurar fonte bold
            font_config = FONT_CONFIGS.get("numero_habilitacao", {"size": 12, "bold": True})
            is_bold = font_config.get("bold", True)
            font_size = font_config.get("size", 12)
            color = font_config.get("color", (0, 0, 0))
            
            # Começar com o tamanho da fonte especificado
            current_font_size = font_size
            font = self._get_font(current_font_size, bold=is_bold)
            
            # Calcular dimensões do texto
            bbox = draw.textbbox((0, 0), numero_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Ajustar fonte para caber na altura disponível (considerando rotação)
            while text_width > area_height - 10 and current_font_size > 6:
                current_font_size -= 1
                font = self._get_font(current_font_size, bold=is_bold)
                bbox = draw.textbbox((0, 0), numero_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            
            # Criar imagem temporária com espaço suficiente
            temp_width = text_width + 20  # margem extra
            temp_height = text_height + 20  # margem extra
            temp_img = Image.new('RGBA', (temp_width, temp_height), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Desenhar texto centralizado na imagem temporária
            text_x = (temp_width - text_width) // 2
            text_y = (temp_height - text_height) // 2
            temp_draw.text((text_x, text_y), numero_text, font=font, fill=color)
            
            # Rotacionar 90 graus para ficar vertical
            rotated_img = temp_img.rotate(90, expand=True)
            
            # Calcular posição final para centralizar na área designada
            final_x = x - (rotated_img.width - area_width) // 2
            final_y = y + (area_height - rotated_img.height) // 2
            
            # Garantir que não saia dos limites
            if final_x < 0:
                final_x = x
            if final_y < 0:
                final_y = y
            
            # Colar na imagem principal
            draw._image.paste(rotated_img, (final_x, final_y), rotated_img)
            
            logger.debug(f"Número habilitação vertical '{numero_text}' desenhado em {position} com fonte {current_font_size}px")
            
        except Exception as e:
            logger.error(f"Erro ao desenhar número habilitação vertical: {str(e)}")
            # Fallback: usar o método de texto rotacionado padrão
            font = self._get_font(10, bold=True)
            self._draw_rotated_text(draw, numero_text, position, font, (0, 0, 0), rotation=90)
    
    def _draw_numero_espelho_vertical(self, draw, numero_text, position):
        """
        Desenha o número do espelho verticalmente no verso, igual ao número da habilitação.
        
        Args:
            draw: Objeto ImageDraw
            numero_text: Texto do número do espelho
            position: Posição (x, y) onde desenhar
        """
        try:
            x, y = position
            area_width = 23
            area_height = 161
            
            # Configurar fonte bold (mesmo estilo do número da habilitação)
            font_config = BACK_FONT_CONFIGS.get("numero_espelho", {"size": 12, "bold": True})
            is_bold = font_config.get("bold", True)
            font_size = font_config.get("size", 12)
            color = font_config.get("color", (0, 0, 0))
            
            # Começar com o tamanho da fonte especificado
            current_font_size = font_size
            font = self._get_font(current_font_size, bold=is_bold)
            
            # Calcular dimensões do texto
            bbox = draw.textbbox((0, 0), numero_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Ajustar fonte para caber na altura disponível (considerando rotação)
            while text_width > area_height - 10 and current_font_size > 6:
                current_font_size -= 1
                font = self._get_font(current_font_size, bold=is_bold)
                bbox = draw.textbbox((0, 0), numero_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            
            # Criar imagem temporária com espaço suficiente
            temp_width = text_width + 20  # margem extra
            temp_height = text_height + 20  # margem extra
            temp_img = Image.new('RGBA', (temp_width, temp_height), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Desenhar texto centralizado na imagem temporária
            text_x = (temp_width - text_width) // 2
            text_y = (temp_height - text_height) // 2
            temp_draw.text((text_x, text_y), numero_text, font=font, fill=color)
            
            # Rotacionar 90 graus para ficar vertical
            rotated_img = temp_img.rotate(90, expand=True)
            
            # Calcular posição final para centralizar na área designada
            final_x = x - (rotated_img.width - area_width) // 2
            final_y = y + (area_height - rotated_img.height) // 2
            
            # Garantir que não saia dos limites
            if final_x < 0:
                final_x = x
            if final_y < 0:
                final_y = y
            
            # Colar na imagem principal
            draw._image.paste(rotated_img, (final_x, final_y), rotated_img)
            
            logger.debug(f"Número espelho vertical '{numero_text}' desenhado em {position} com fonte {current_font_size}px")
            
        except Exception as e:
            logger.error(f"Erro ao desenhar número espelho vertical: {str(e)}")
            # Fallback: usar o método de texto rotacionado padrão
            font = self._get_font(10, bold=True)
            self._draw_rotated_text(draw, numero_text, position, font, (0, 0, 0), rotation=90)
    
    def _process_foto_3x4(self, main_image, cnh_request):
        """
        Processa e insere foto 3x4 na CNH se fornecida.
        
        Args:
            main_image: Imagem principal da CNH
            cnh_request: Objeto CNHRequest com dados
        """
        try:
            # Verificar se há caminho para foto 3x4
            if not hasattr(cnh_request, 'foto_3x4_path') or not cnh_request.foto_3x4_path:
                logger.debug("Nenhuma foto 3x4 fornecida")
                return
                
            foto_path = cnh_request.foto_3x4_path
            if not os.path.exists(foto_path):
                logger.warning(f"Foto 3x4 não encontrada: {foto_path}")
                return
            
            # Carregar e redimensionar foto 3x4
            foto_3x4 = Image.open(foto_path)
            foto_width = FOTO_3X4_AREA["width"]
            foto_height = FOTO_3X4_AREA["height"]
            
            # Redimensionar mantendo proporção e cortando se necessário
            foto_3x4 = self._resize_and_crop_image(foto_3x4, foto_width, foto_height)
            
            # Colar foto na posição correta
            position = FOTO_3X4_AREA["position"]
            main_image.paste(foto_3x4, position)
            
            logger.info(f"Foto 3x4 inserida em {position} com dimensões {foto_width}x{foto_height}")
            
        except Exception as e:
            logger.error(f"Erro ao processar foto 3x4: {str(e)}")
    
    def _process_signature(self, main_image, cnh_request):
        """
        Processa e insere assinatura na CNH se fornecida.
        
        Args:
            main_image: Imagem principal da CNH
            cnh_request: Objeto CNHRequest com dados
        """
        try:
            # Verificar se há caminho para assinatura
            if not hasattr(cnh_request, 'assinatura_path') or not cnh_request.assinatura_path:
                logger.debug("Nenhuma assinatura fornecida")
                return
                
            assinatura_path = cnh_request.assinatura_path
            if not os.path.exists(assinatura_path):
                logger.warning(f"Assinatura não encontrada: {assinatura_path}")
                return
            
            # Carregar assinatura original
            signature = Image.open(assinatura_path)
            logger.info(f"Assinatura carregada: {signature.size}, modo: {signature.mode}")
            
            sig_width = ASSINATURA_AREA["width"]
            sig_height = ASSINATURA_AREA["height"]
            
            # Redimensionar assinatura para tamanho exato (sem cortar)
            signature = self._resize_signature_exact(signature, sig_width, sig_height)
            
            # Colar assinatura preservando transparência
            if signature.mode == 'RGBA':
                main_image.paste(signature, ASSINATURA_AREA["position"], signature)
                logger.info("✅ Assinatura colada com transparência preservada")
            else:
                main_image.paste(signature, ASSINATURA_AREA["position"])
                logger.info("⚠️ Assinatura colada sem transparência")
            
            logger.info(f"Assinatura inserida em {ASSINATURA_AREA['position']} com dimensões {sig_width}x{sig_height}")
            
        except Exception as e:
            logger.error(f"Erro ao processar assinatura: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _resize_signature_exact(self, image, target_width, target_height):
        """
        Redimensiona assinatura para tamanho exato SEM cortar.
        Preserva todo o conteúdo da assinatura, incluindo transparência.
        
        Args:
            image: Imagem PIL da assinatura
            target_width: Largura desejada
            target_height: Altura desejada
            
        Returns:
            Image: Imagem redimensionada para tamanho exato com transparência preservada
        """
        try:
            logger.info(f"Redimensionando assinatura: {image.size} -> {target_width}x{target_height}")
            logger.info(f"Modo da imagem original: {image.mode}")
            
            # Garantir que a imagem tenha transparência (RGBA)
            if image.mode != 'RGBA':
                logger.info("Convertendo imagem para RGBA para preservar transparência")
                image = image.convert('RGBA')
            
            # Redimensionar diretamente para o tamanho exato preservando transparência
            resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            logger.info(f"Assinatura redimensionada com sucesso para {resized.size}, modo: {resized.mode}")
            return resized
            
        except Exception as e:
            logger.error(f"Erro ao redimensionar assinatura: {str(e)}")
            raise e
    
    def _resize_and_crop_image(self, image, target_width, target_height):
        """
        Redimensiona e corta imagem para o tamanho exato mantendo proporção.
        USADO APENAS PARA FOTOS 3X4 - corta excesso para manter proporção.
        
        Args:
            image: Imagem PIL
            target_width: Largura desejada
            target_height: Altura desejada
            
        Returns:
            Image: Imagem redimensionada e cortada
        """
        # Calcular proporções
        img_ratio = image.width / image.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            # Imagem é mais larga - cortar largura
            new_height = target_height
            new_width = int(target_height * img_ratio)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Cortar centro
            left = (new_width - target_width) // 2
            cropped = resized.crop((left, 0, left + target_width, target_height))
        else:
            # Imagem é mais alta - cortar altura
            new_width = target_width
            new_height = int(target_width / img_ratio)
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Cortar centro
            top = (new_height - target_height) // 2
            cropped = resized.crop((0, top, target_width, top + target_height))
        
        return cropped
    
    def _draw_header(self, draw, cnh_request):
        """Desenha cabeçalho da CNH."""
        # Fundo do cabeçalho com gradiente simulado
        header_height = 100
        
        # Gradiente simulado com múltiplas linhas
        for i in range(header_height):
            opacity = 1.0 - (i / header_height) * 0.3
            color = tuple(int(c * opacity) for c in self.HEADER_COLOR)
            draw.line([(0, i), (self.IMAGE_WIDTH, i)], fill=color, width=1)
        
        # Bordas do cabeçalho
        draw.rectangle([0, 0, self.IMAGE_WIDTH, header_height], outline=self.BORDER_COLOR, width=2)
        
        # Logo simulado (círculo)
        logo_size = 40
        logo_x = 30
        logo_y = 30
        draw.ellipse([logo_x, logo_y, logo_x + logo_size, logo_y + logo_size], 
                    fill=(255, 255, 255), outline=self.BORDER_COLOR, width=2)
        
        # Brasão simulado no logo
        center_x = logo_x + logo_size // 2
        center_y = logo_y + logo_size // 2
        draw.text((center_x - 8, center_y - 8), "BR", fill=self.HEADER_COLOR, font=self.small_font)
        
        # Título principal
        title = "CARTEIRA NACIONAL DE HABILITAÇÃO"
        title_bbox = draw.textbbox((0, 0), title, font=self.header_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.IMAGE_WIDTH - title_width) // 2
        draw.text((title_x, 25), title, fill=(255, 255, 255), font=self.header_font)
        
        # Subtítulo
        subtitle = "REPÚBLICA FEDERATIVA DO BRASIL"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=self.small_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.IMAGE_WIDTH - subtitle_width) // 2
        draw.text((subtitle_x, 65), subtitle, fill=(255, 255, 255), font=self.small_font)
        
        # Número de série no canto superior direito
        serial = f"Série: {cnh_request.id:06d}"
        serial_bbox = draw.textbbox((0, 0), serial, font=self.small_font)
        serial_width = serial_bbox[2] - serial_bbox[0]
        draw.text((self.IMAGE_WIDTH - serial_width - 20, 15), serial, 
                 fill=(255, 255, 255, 200), font=self.small_font)
    
    def _draw_photo_placeholder(self, draw):
        """Desenha placeholder para foto com bordas profissionais."""
        # Posição da foto (canto superior direito)
        photo_x = self.IMAGE_WIDTH - 140
        photo_y = 120
        photo_width = 100
        photo_height = 130
        
        # Sombra da foto
        shadow_offset = 3
        draw.rectangle([photo_x + shadow_offset, photo_y + shadow_offset, 
                       photo_x + photo_width + shadow_offset, photo_y + photo_height + shadow_offset], 
                      fill=(0, 0, 0, 50))
        
        # Fundo da foto
        draw.rectangle([photo_x, photo_y, photo_x + photo_width, photo_y + photo_height], 
                      fill=(245, 245, 245), outline=self.BORDER_COLOR, width=2)
        
        # Borda interna
        draw.rectangle([photo_x + 3, photo_y + 3, photo_x + photo_width - 3, photo_y + photo_height - 3], 
                      outline=self.ACCENT_COLOR, width=1)
        
        # Ícone de pessoa
        person_icon = "👤"  # Emoji como placeholder
        person_bbox = draw.textbbox((0, 0), person_icon, font=self.header_font)
        person_width = person_bbox[2] - person_bbox[0]
        person_height = person_bbox[3] - person_bbox[1]
        
        icon_x = photo_x + (photo_width - person_width) // 2
        icon_y = photo_y + (photo_height - person_height) // 2 - 10
        draw.text((icon_x, icon_y), person_icon, font=self.header_font)
        
        # Texto "FOTO" abaixo do ícone
        photo_text = "FOTO"
        photo_text_bbox = draw.textbbox((0, 0), photo_text, font=self.small_font)
        photo_text_width = photo_text_bbox[2] - photo_text_bbox[0]
        
        text_x = photo_x + (photo_width - photo_text_width) // 2
        text_y = icon_y + 40
        draw.text((text_x, text_y), photo_text, fill=self.TEXT_COLOR, font=self.small_font)
    
    def _draw_personal_data(self, draw, cnh_request):
        """Desenha dados pessoais com layout melhorado incluindo todos os novos campos."""
        # Seção de dados pessoais (maior para acomodar mais campos)
        section_y = 120
        section_height = 280
        section_x = 30
        section_width = 550
        
        # Fundo da seção
        draw.rectangle([section_x, section_y, section_x + section_width, section_y + section_height], 
                      fill=(255, 255, 255), outline=self.BORDER_COLOR, width=1)
        
        # Título da seção
        section_title = "DADOS PESSOAIS"
        draw.text((section_x + 10, section_y + 10), section_title, 
                 fill=self.HEADER_COLOR, font=self.title_font)
        
        # Linha divisória
        draw.line([section_x + 10, section_y + 35, section_x + section_width - 10, section_y + 35], 
                 fill=self.ACCENT_COLOR, width=2)
        
        # Dados em duas colunas
        start_y = section_y + 50
        line_height = 25
        col1_x = section_x + 15
        col2_x = section_x + 280
        
        # Coluna 1 - Dados principais
        nome = cnh_request.nome_completo or "NÃO INFORMADO"
        self._draw_modern_field(draw, "NOME COMPLETO", nome.upper(), 
                               col1_x, start_y, 250)
        
        cpf = cnh_request.cpf or "NÃO INFORMADO"
        self._draw_modern_field(draw, "CPF", cpf, 
                               col1_x, start_y + line_height, 120)
        
        # Documento de identidade
        doc_numero = cnh_request.doc_identidade_numero or "NÃO INFORMADO"
        doc_orgao = cnh_request.doc_identidade_orgao or "SSP"
        doc_uf = cnh_request.doc_identidade_uf or "SP"
        doc_completo = f"{doc_numero} {doc_orgao}/{doc_uf}"
        self._draw_modern_field(draw, "IDENTIDADE", doc_completo, 
                               col1_x, start_y + line_height * 2, 200)
        
        # Nacionalidade (sempre fixo)
        nacionalidade = "BRASILEIRO(A)"  # String fixa sempre
        self._draw_modern_field(draw, "NACIONALIDADE", nacionalidade.upper(), 
                               col1_x, start_y + line_height * 3, 150)
        
        # Sexo
        sexo = cnh_request.sexo_condutor or "M"
        sexo_descricao = "MASCULINO" if sexo == "M" else "FEMININO" if sexo == "F" else "NÃO INFORMADO"
        self._draw_modern_field(draw, "SEXO", sexo_descricao, 
                               col1_x, start_y + line_height * 4, 100)
        
        # Nome dos pais
        nome_pai = cnh_request.nome_pai or "NÃO INFORMADO"
        self._draw_modern_field(draw, "NOME DO PAI", nome_pai.upper() if nome_pai != "NÃO INFORMADO" else nome_pai, 
                               col1_x, start_y + line_height * 5, 250)
        
        nome_mae = cnh_request.nome_mae or "NÃO INFORMADO"
        self._draw_modern_field(draw, "NOME DA MÃE", nome_mae.upper() if nome_mae != "NÃO INFORMADO" else nome_mae, 
                               col1_x, start_y + line_height * 6, 250)
        
        # Coluna 2 - Datas e local (data de nascimento agora concatenada na coordenada principal)
        # Data de nascimento movida para coordenada (483, 171) concatenada com local e UF
        if cnh_request.data_nascimento:
            idade = cnh_request.get_idade()
        else:
            idade = 0
        
        # self._draw_modern_field(draw, "DATA NASCIMENTO", data_nasc_formatada, 
        #                        col2_x, start_y, 100)  # Removido - agora concatenado
        
        self._draw_modern_field(draw, "IDADE", f"{idade} anos" if idade > 0 else "NÃO CALC.", 
                               col2_x, start_y, 80)  # Movido para start_y (posição da data)
        
        # Primeira habilitação (movida para cima)
        if cnh_request.primeira_habilitacao:
            primeira_hab = cnh_request.primeira_habilitacao.strftime("%d/%m/%Y")
        else:
            primeira_hab = "NÃO INFORMADA"
        self._draw_modern_field(draw, "1ª HABILITAÇÃO", primeira_hab, 
                               col2_x, start_y + line_height, 120)  # Movido para line_height (posição da idade)
        
        # Local de nascimento (agora concatenado no campo principal)
        # Removido daqui pois está sendo exibido concatenado com data na coordenada (483, 171)
        # local_nasc = cnh_request.local_nascimento or "NÃO INFORMADO"
        # uf_nasc = cnh_request.uf_nascimento or ""
        # local_completo = f"{local_nasc}/{uf_nasc}" if uf_nasc else local_nasc
        # self._draw_modern_field(draw, "LOCAL NASCIMENTO", local_completo.upper(), 
        #                        col2_x, start_y + line_height * 2, 150)
        
        # Categoria destacada
        categoria = cnh_request.categoria_habilitacao or "B"
        cat_y = start_y + line_height * 7
        self._draw_category_highlight(draw, categoria, col1_x, cat_y)
    
    def _draw_cnh_details(self, draw, cnh_request):
        """Desenha detalhes específicos da CNH com layout moderno incluindo novos campos."""
        # Seção de detalhes da CNH (aumentada para novos campos)
        section_y = 420
        section_height = 160
        section_x = 30
        section_width = 550
        
        # Fundo da seção
        draw.rectangle([section_x, section_y, section_x + section_width, section_y + section_height], 
                      fill=(248, 249, 250), outline=self.BORDER_COLOR, width=1)
        
        # Título da seção
        section_title = "INFORMAÇÕES DA HABILITAÇÃO"
        draw.text((section_x + 10, section_y + 10), section_title, 
                 fill=self.HEADER_COLOR, font=self.title_font)
        
        # Linha divisória
        draw.line([section_x + 10, section_y + 35, section_x + section_width - 10, section_y + 35], 
                 fill=self.ACCENT_COLOR, width=2)
        
        # Dados em layout moderno
        start_y = section_y + 50
        line_height = 25
        col1_x = section_x + 15
        col2_x = section_x + 190
        col3_x = section_x + 380
        
        # Primeira linha - Números de controle
        numero_registro = cnh_request.numero_registro or f"{cnh_request.id:011d}"
        self._draw_modern_field(draw, "Nº REGISTRO", numero_registro, col1_x, start_y, 150)
        
        numero_espelho = cnh_request.numero_espelho or f"{cnh_request.id:011d}"
        self._draw_modern_field(draw, "Nº ESPELHO", numero_espelho, col2_x, start_y, 150)
        
        # RENACH
        uf_cnh = cnh_request.uf_cnh or "SP"
        numero_renach = cnh_request.numero_renach or f"{uf_cnh}{cnh_request.id:09d}"
        self._draw_modern_field(draw, "RENACH", numero_renach, col3_x, start_y, 120)
        
        # Segunda linha - Datas
        start_y2 = start_y + line_height
        
        # Data de emissão (usar campo específico se disponível)
        if cnh_request.data_emissao:
            data_emissao = cnh_request.data_emissao.strftime("%d/%m/%Y")
        else:
            data_emissao = cnh_request.created_at.strftime("%d/%m/%Y")
        self._draw_modern_field(draw, "EMISSÃO", data_emissao, col1_x, start_y2, 100)
        
        # Data de validade (usar campo específico se disponível)
        if cnh_request.validade:
            data_validade = cnh_request.validade.strftime("%d/%m/%Y")
        else:
            from datetime import timedelta
            data_validade = (cnh_request.created_at + timedelta(days=365*5)).strftime("%d/%m/%Y")
        self._draw_modern_field(draw, "VALIDADE", data_validade, col2_x, start_y2, 100)
        
        # UF da CNH
        self._draw_modern_field(draw, "UF", uf_cnh, col3_x, start_y2, 50)
        
        # Terceira linha - Local e órgão
        start_y3 = start_y2 + line_height
        
        # Local de emissão
        local_municipio = cnh_request.local_municipio or "SÃO PAULO"
        local_uf = cnh_request.local_uf or uf_cnh
        local_completo = f"{local_municipio}/{local_uf}"
        self._draw_modern_field(draw, "LOCAL EMISSÃO", local_completo.upper(), col1_x, start_y3, 180)
        
        # Órgão emissor
        orgao_emissor = f"DETRAN/{uf_cnh}"
        self._draw_modern_field(draw, "ÓRGÃO EMISSOR", orgao_emissor, col2_x, start_y3, 120)
        
        # Código de validação
        codigo_validacao = cnh_request.codigo_validacao or f"{cnh_request.id:010d}"
        self._draw_modern_field(draw, "CÓD. VALIDAÇÃO", codigo_validacao, col3_x, start_y3, 120)
        
        # Quarta linha - ACC e observações
        start_y4 = start_y3 + line_height
        
        # ACC (Categoria especial)
        acc = cnh_request.acc or "NAO"
        acc_text = "SIM" if acc == "SIM" else "NÃO"
        self._draw_modern_field(draw, "ACC", acc_text, col1_x, start_y4, 80)
        
        # Observações (se houver)
        if cnh_request.observacoes:
            obs_resumida = cnh_request.observacoes[:30] + "..." if len(cnh_request.observacoes) > 30 else cnh_request.observacoes
            self._draw_modern_field(draw, "OBSERVAÇÕES", obs_resumida.upper(), col2_x, start_y4, 200)
        else:
            self._draw_modern_field(draw, "OBSERVAÇÕES", "NENHUMA", col2_x, start_y4, 200)
    
    def _draw_footer(self, draw, cnh_request):
        """Desenha rodapé com informações adicionais e elementos de segurança."""
        footer_y = self.IMAGE_HEIGHT - 50
        
        # Fundo do rodapé
        draw.rectangle([0, footer_y - 5, self.IMAGE_WIDTH, self.IMAGE_HEIGHT], 
                      fill=(240, 240, 240), outline=self.BORDER_COLOR, width=1)
        
        # Linha decorativa
        draw.line([30, footer_y + 5, self.IMAGE_WIDTH - 30, footer_y + 5], 
                 fill=self.ACCENT_COLOR, width=2)
        
        # Elementos de segurança simulados
        security_elements = ["🔒", "🛡️", "✓"]
        for i, element in enumerate(security_elements):
            x = 50 + i * 30
            draw.text((x, footer_y + 15), element, font=self.small_font)
        
        # Texto de rodapé
        footer_text = "DOCUMENTO GERADO ELETRONICAMENTE • VÁLIDO EM TODO TERRITÓRIO NACIONAL"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=self.small_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (self.IMAGE_WIDTH - footer_width) // 2
        draw.text((footer_x, footer_y + 15), footer_text, fill=self.TEXT_COLOR, font=self.small_font)
        
        # Data/hora de geração
        timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        timestamp_text = f"Emitido em: {timestamp}"
        timestamp_bbox = draw.textbbox((0, 0), timestamp_text, font=self.small_font)
        timestamp_width = timestamp_bbox[2] - timestamp_bbox[0]
        timestamp_x = (self.IMAGE_WIDTH - timestamp_width) // 2
        draw.text((timestamp_x, footer_y + 35), timestamp_text, fill=self.BORDER_COLOR, font=self.small_font)
        
        # Código de verificação simulado
        verification_code = f"Cód. Verificação: {cnh_request.id:06d}-{hash(cnh_request.cpf) % 10000:04d}"
        verification_bbox = draw.textbbox((0, 0), verification_code, font=self.small_font)
        verification_width = verification_bbox[2] - verification_bbox[0]
        verification_x = (self.IMAGE_WIDTH - verification_width) // 2
        draw.text((verification_x, footer_y + 50), verification_code, fill=self.BORDER_COLOR, font=self.small_font)
    
    def _draw_modern_field(self, draw, label, value, x, y, width):
        """
        Desenha um campo moderno com estilo profissional.
        
        Args:
            draw: Objeto ImageDraw
            label: Rótulo do campo
            value: Valor do campo
            x: Posição X
            y: Posição Y
            width: Largura do campo
        """
        # Label em cinza pequeno
        draw.text((x, y), label, fill=self.BORDER_COLOR, font=self.small_font)
        
        # Valor em negrito
        draw.text((x, y + 12), str(value), fill=self.TEXT_COLOR, font=self.data_font)
        
        # Linha de base
        draw.line([x, y + 32, x + width, y + 32], fill=self.BORDER_COLOR, width=1)
    
    def _draw_category_highlight(self, draw, categoria, x, y):
        """Desenha categoria com destaque especial."""
        # Fundo destacado
        cat_width = 200
        cat_height = 40
        
        draw.rectangle([x, y, x + cat_width, y + cat_height], 
                      fill=self.ACCENT_COLOR, outline=self.ACCENT_COLOR, width=2)
        
        # Texto da categoria
        cat_text = f"CATEGORIA {categoria}"
        cat_bbox = draw.textbbox((0, 0), cat_text, font=self.title_font)
        cat_text_width = cat_bbox[2] - cat_bbox[0]
        
        text_x = x + (cat_width - cat_text_width) // 2
        text_y = y + 12
        draw.text((text_x, text_y), cat_text, fill=(255, 255, 255), font=self.title_font)
    
    def _generate_filename(self, cnh_request, file_type="cnh"):
        """
        Gera nome simples e intuitivo para arquivo da CNH.
        
        Args:
            cnh_request: Objeto CNHRequest
            file_type: Tipo do arquivo (cnh_front, cnh_back, qr_code)
            
        Returns:
            str: Nome do arquivo
        """
        # Nome simples: apenas o ID da CNH
        # Como está em pastas organizadas por usuário e tipo, não precisa ser complexo
        filename = f"{cnh_request.id}.png"
        return filename
    
    def get_cnh_paths(self, cnh_request):
        """
        Gera os paths organizados para todos os tipos de imagem CNH baseados no CPF.
        
        Args:
            cnh_request: Objeto CNHRequest
            
        Returns:
            dict: Dicionário com paths da frente, verso e QR code
        """
        # Nome simples: apenas ID.png
        filename = f"{cnh_request.id}.png"
        
        # Limpar CPF (remover pontos e traços)
        cpf_limpo = ''.join(filter(str.isdigit, cnh_request.cpf)) if cnh_request.cpf else f"user_{cnh_request.user_id}"
        
        # Diretórios específicos por tipo
        front_dir = self._ensure_cnh_directory(cnh_request, "front")
        back_dir = self._ensure_cnh_directory(cnh_request, "back")
        qrcode_dir = self._ensure_cnh_directory(cnh_request, "qrcode")
        
        return {
            "front_path": os.path.join(front_dir, filename),
            "back_path": os.path.join(back_dir, filename),
            "qrcode_path": os.path.join(qrcode_dir, filename),
            "front_relative": f"static/uploads/cnh/{cpf_limpo}/front/{filename}",
            "back_relative": f"static/uploads/cnh/{cpf_limpo}/back/{filename}",
            "qrcode_relative": f"static/uploads/cnh/{cpf_limpo}/qrcode/{filename}"
        }
    
    def generate_thumbnail(self, image_path, max_size=(200, 150)):
        """
        Gera thumbnail da imagem CNH.
        
        Args:
            image_path: Caminho da imagem original
            max_size: Tamanho máximo do thumbnail
            
        Returns:
            str: Caminho do thumbnail
        """
        try:
            # Abrir imagem original
            with Image.open(image_path) as img:
                # Criar thumbnail
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Gerar nome do thumbnail
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                thumb_filename = f"{base_name}_thumb.png"
                thumb_path = os.path.join(self.OUTPUT_DIR, thumb_filename)
                
                # Salvar thumbnail
                img.save(thumb_path, 'PNG')
                
                logger.info(f"Thumbnail gerado: {thumb_path}")
                return thumb_path
                
        except Exception as e:
            logger.error(f"Erro ao gerar thumbnail: {str(e)}")
            return None
    
    def validate_image(self, image_path):
        """
        Valida se imagem foi gerada corretamente.
        
        Args:
            image_path: Caminho da imagem
            
        Returns:
            bool: True se imagem é válida
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Arquivo não existe: {image_path}")
                return False
            
            # Verificar se arquivo não está vazio
            file_size = os.path.getsize(image_path)
            if file_size == 0:
                logger.error(f"Arquivo vazio: {image_path}")
                return False
            
            logger.info(f"Validando imagem: {image_path}, tamanho: {file_size} bytes")
            
            # Tentar abrir imagem
            with Image.open(image_path) as img:
                # Verificar se a imagem tem dimensões razoáveis (não validar dimensões específicas)
                width, height = img.size
                if width < 400 or height < 300 or width > 1000 or height > 800:
                    logger.error(f"Dimensões fora do intervalo válido: {img.size}")
                    return False
                logger.info(f"Dimensões da imagem: {img.size}")
                
                # Verificar formato
                if img.format != 'PNG':
                    logger.error(f"Formato inválido: {img.format}, esperado: PNG")
                    return False
            
            logger.info(f"Imagem válida: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar imagem: {str(e)}")
            return False

    # ==================== MÉTODOS PARA VERSO DA CNH ====================
    
    def generate_back_cnh(self, cnh_request, output_path=None):
        """
        Gera o VERSO da CNH usando coordenadas específicas.
        
        Args:
            cnh_request: Objeto CNHRequest com dados
            output_path: Caminho específico para salvar (opcional)
            
        Returns:
            str: Caminho do arquivo gerado
        """
        try:
            logger.info(f"Iniciando geração do VERSO da CNH - ID: {cnh_request.id}")
            
            # Carregar template do verso
            template_path = os.path.join(os.path.dirname(__file__), '..', BACK_TEMPLATE_PATH)
            if not os.path.exists(template_path):
                logger.warning(f"Template do verso não encontrado: {template_path}. Usando imagem em branco.")
                image = Image.new('RGB', (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), (255, 255, 255))
            else:
                image = Image.open(template_path).copy()
            
            draw = ImageDraw.Draw(image)
            
            # Aplicar dados usando coordenadas do verso
            self._apply_back_data_with_coordinates(draw, cnh_request)
            
            # Usar path específico ou gerar automaticamente
            if output_path:
                filepath = output_path
                # Garantir que o diretório existe
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            else:
                # Criar diretório da CNH e gerar nome único para arquivo do verso
                cnh_dir = self._ensure_cnh_directory(cnh_request, "cnh_back")
                filename = self._generate_filename(cnh_request, "cnh_back")
                filepath = os.path.join(cnh_dir, filename)
            
            # Salvar imagem
            image.save(filepath, 'PNG', quality=95)
            
            logger.info(f"Verso da CNH gerado com sucesso - Arquivo: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao gerar verso da CNH - ID: {cnh_request.id}, Erro: {str(e)}")
            raise e
    
    def _apply_back_data_with_coordinates(self, draw, cnh_request):
        """
        Aplica os dados do VERSO da CNH usando coordenadas específicas do verso.
        
        Args:
            draw: Objeto ImageDraw
            cnh_request: Objeto CNHRequest com dados
        """
        try:
            # Função auxiliar para desenhar campo do verso
            def draw_back_field_if_exists(field_name, text):
                if text and field_name in CNH_BACK_COORDINATES and field_name in BACK_FONT_CONFIGS:
                    coord = CNH_BACK_COORDINATES[field_name]
                    font_config = BACK_FONT_CONFIGS[field_name]
                    is_bold = font_config.get("bold", False)
                    font = self._get_font(font_config["size"], bold=is_bold)
                    
                    draw.text(coord, str(text), fill=font_config["color"], font=font)
                    logger.debug(f"Campo verso '{field_name}' desenhado: '{text}' em {coord}")
                    return True
                return False
            
            # INFORMAÇÕES TÉCNICAS
            logger.info(f"🔍 DEBUG VERSO - ID: {cnh_request.id}")
            logger.info(f"   numero_renach: '{cnh_request.numero_renach}'")
            logger.info(f"   codigo_validacao: '{cnh_request.codigo_validacao}'")
            logger.info(f"   numero_espelho: '{cnh_request.numero_espelho}'")
            logger.info(f"   numero_registro: '{cnh_request.numero_registro}'")
            
            draw_back_field_if_exists("numero_renach", cnh_request.numero_renach)
            draw_back_field_if_exists("codigo_validacao", cnh_request.codigo_validacao)
            
            # NÚMERO DO ESPELHO (vertical como na frente)
            numero_espelho = cnh_request.numero_espelho or f"{cnh_request.id + 1000000000:011d}"
            if numero_espelho:
                espelho_coord = CNH_BACK_COORDINATES.get("numero_espelho", (100, 80))
                self._draw_numero_espelho_vertical(draw, str(numero_espelho), espelho_coord)
            
            # NÚMERO DO REGISTRO DA CNH (lateral esquerda)
            draw_back_field_if_exists("numero_registro", cnh_request.numero_registro)
            
            # OBSERVAÇÕES
            draw_back_field_if_exists("observacoes", cnh_request.observacoes)
            
            # LOCAL DA HABILITAÇÃO
            draw_back_field_if_exists("local_habilitacao", cnh_request.local_municipio)
            draw_back_field_if_exists("uf_habilitacao", cnh_request.local_uf)
            
            # HISTÓRICO DE CATEGORIAS (CATEGORIA A)
            self._draw_category_history(draw, cnh_request)
            
            # CÓDIGOS DE SEGURANÇA
            self._draw_security_codes(draw, cnh_request)
            
            # INFORMAÇÕES DO SISTEMA
            data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
            draw_back_field_if_exists("data_geracao", f"Gerado: {data_geracao}")
            draw_back_field_if_exists("versao_sistema", "V2.0")
            
            logger.info(f"Dados do verso aplicados com sucesso - ID: {cnh_request.id}")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar dados do verso: {str(e)}")
            raise e
    
    def _draw_category_history(self, draw, cnh_request):
        """Desenha o histórico de categorias no verso - FOCO NA CATEGORIA A."""
        try:
            # Se é categoria A, desenhar a data nas coordenadas específicas
            if cnh_request.categoria_habilitacao == "A" and cnh_request.primeira_habilitacao:
                field_name = "categoria_a_data"
                if field_name in CNH_BACK_COORDINATES and field_name in BACK_FONT_CONFIGS:
                    coord = CNH_BACK_COORDINATES[field_name]
                    font_config = BACK_FONT_CONFIGS[field_name]
                    font = self._get_font(font_config["size"])
                    data_str = cnh_request.primeira_habilitacao.strftime("%d/%m/%Y")
                    
                    draw.text(coord, data_str, fill=font_config["color"], font=font)
                    logger.info(f"✅ CATEGORIA A: data '{data_str}' desenhada em {coord}")
                else:
                    logger.warning(f"❌ Coordenadas para categoria A não encontradas!")
            
            # Outras categorias se necessário
            categoria = cnh_request.categoria_habilitacao
            if categoria in ["B", "C", "D", "E"] and cnh_request.primeira_habilitacao:
                field_name = f"categoria_{categoria.lower()}_data"
                if field_name in CNH_BACK_COORDINATES:
                    coord = CNH_BACK_COORDINATES[field_name]
                    font_config = BACK_FONT_CONFIGS.get(field_name, {"size": 9, "color": (0, 0, 0)})
                    font = self._get_font(font_config["size"])
                    data_str = cnh_request.primeira_habilitacao.strftime("%d/%m/%Y")
                    draw.text(coord, data_str, fill=font_config["color"], font=font)
                    logger.info(f"Categoria {categoria}: data '{data_str}' desenhada em {coord}")
                    
        except Exception as e:
            logger.error(f"Erro ao desenhar histórico de categorias: {str(e)}")
    
    def _draw_security_codes(self, draw, cnh_request):
        """Gera códigos de segurança simples."""
        try:
            import hashlib
            
            # Código baseado no ID da CNH
            base_string = f"{cnh_request.id}{cnh_request.cpf or 'DEFAULT'}"
            code = hashlib.md5(base_string.encode()).hexdigest()[:8].upper()
            
            # Desenhar se existe coordenada
            if "codigo_seguranca_1" in CNH_BACK_COORDINATES:
                coord = CNH_BACK_COORDINATES["codigo_seguranca_1"]
                font_config = BACK_FONT_CONFIGS.get("codigo_seguranca_1", {"size": 8, "color": (128, 128, 128)})
                font = self._get_font(font_config["size"])
                draw.text(coord, code, fill=font_config["color"], font=font)
                
        except Exception as e:
            logger.error(f"Erro ao gerar códigos de segurança: {str(e)}")
    

    
    def generate_complete_cnh(self, cnh_request):
        """
        Gera CNH COMPLETA (frente + verso).
        
        Returns:
            tuple: (front_path: str, back_path: str)
        """
        try:
            logger.info(f"Iniciando geração COMPLETA da CNH - ID: {cnh_request.id}")
            
            # Gerar frente
            front_path = self.generate_basic_cnh(cnh_request)
            
            # Gerar verso 
            back_path = self.generate_back_cnh(cnh_request)
            
            logger.info(f"CNH completa gerada - Frente: {front_path}, Verso: {back_path}")
            return front_path, back_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar CNH completa - ID: {cnh_request.id}, Erro: {str(e)}")
            raise e

# ==================== FUNÇÃO PRINCIPAL ====================

def gerar_cnh_basica(cnh_request):
    """
    Função principal para gerar CNH básica com estrutura organizada.
    
    Args:
        cnh_request: Objeto CNHRequest
        
    Returns:
        tuple: (success: bool, paths_dict: dict, error_message: str)
        paths_dict contém: front_path, back_path, qrcode_path (relativos)
    """
    try:
        generator = CNHImageGenerator()
        
        # Marcar como processando
        cnh_request.marcar_como_processando()
        
        # Obter paths organizados
        paths = generator.get_cnh_paths(cnh_request)
        
        # Gerar frente e verso usando paths específicos
        front_path = generator.generate_basic_cnh(cnh_request, paths["front_path"])
        back_path = generator.generate_back_cnh(cnh_request, paths["back_path"])
        
        # Validar imagens geradas
        if not generator.validate_image(front_path):
            error_msg = "Imagem da frente é inválida"
            cnh_request.marcar_como_falha(error_msg)
            return False, None, error_msg
            
        if not generator.validate_image(back_path):
            error_msg = "Imagem do verso é inválida"
            cnh_request.marcar_como_falha(error_msg)
            return False, None, error_msg
        
        # Preparar paths relativos para retorno
        result_paths = {
            "front_path": front_path,
            "back_path": back_path,
            "qrcode_path": paths["qrcode_path"],
            "front_relative": paths["front_relative"],
            "back_relative": paths["back_relative"],
            "qrcode_relative": paths["qrcode_relative"]
        }
        
        # Marcar como completa com path da frente (compatibilidade)
        cnh_request.marcar_como_completa(front_path)
        
        logger.info(f"CNH gerada com sucesso - ID: {cnh_request.id}")
        logger.info(f"  Frente: {front_path}")
        logger.info(f"  Verso: {back_path}")
        
        return True, result_paths, ""
        
    except Exception as e:
        error_msg = f"Erro na geração: {str(e)}"
        cnh_request.marcar_como_falha(error_msg)
        logger.error(f"Erro ao gerar CNH - ID: {cnh_request.id}, Erro: {error_msg}")
        return False, None, error_msg

def gerar_cnh_completa(cnh_request):
    """
    Função para gerar CNH COMPLETA (frente + verso).
    
    Args:
        cnh_request: Objeto CNHRequest
        
    Returns:
        tuple: (success: bool, paths: dict, error_message: str)
    """
    try:
        generator = CNHImageGenerator()
        
        # Marcar como processando
        cnh_request.marcar_como_processando()
        
        # Gerar CNH completa
        front_path, back_path = generator.generate_complete_cnh(cnh_request)
        
        # Validar ambas as imagens
        if not generator.validate_image(front_path):
            error_msg = "Imagem da frente inválida"
            cnh_request.marcar_como_falha(error_msg)
            return False, None, error_msg
            
        if not generator.validate_image(back_path):
            error_msg = "Imagem do verso inválida"
            cnh_request.marcar_como_falha(error_msg)
            return False, None, error_msg
        
        # Marcar como completa
        cnh_request.marcar_como_completa(front_path)
        
        paths = {
            "front": front_path,
            "back": back_path
        }
        
        logger.info(f"CNH completa gerada com sucesso - ID: {cnh_request.id}")
        return True, paths, ""
        
    except Exception as e:
        error_msg = f"Erro na geração completa: {str(e)}"
        cnh_request.marcar_como_falha(error_msg)
        logger.error(f"Erro ao gerar CNH completa - ID: {cnh_request.id}, Erro: {error_msg}")
        return False, None, error_msg 