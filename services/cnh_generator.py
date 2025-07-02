# services/cnh_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime, date
import logging
import uuid
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from static.cnh_matriz.coordinates import CNH_COORDINATES, FONT_CONFIGS, TEMPLATE_PATH

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
    OUTPUT_DIR = "static/generated_cnhs"
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
    
    def _load_fonts(self):
        """Carrega fontes para uso na imagem."""
        try:
            # Tentar carregar fonte personalizada (se existir)
            title_font_path = os.path.join(self.FONTS_DIR, "arial_bold.ttf")
            if os.path.exists(title_font_path):
                self.title_font = ImageFont.truetype(title_font_path, 24)
                self.header_font = ImageFont.truetype(title_font_path, 32)
            else:
                # Usar fonte padrão do sistema
                try:
                    self.title_font = ImageFont.truetype("arial.ttf", 24)
                    self.header_font = ImageFont.truetype("arial.ttf", 32)
                except:
                    # Fallback para fonte padrão do Pillow
                    self.title_font = ImageFont.load_default()
                    self.header_font = ImageFont.load_default()
            
            # Fonte para dados
            try:
                self.data_font = ImageFont.truetype("arial.ttf", 18)
                self.small_font = ImageFont.truetype("arial.ttf", 14)
            except:
                self.data_font = ImageFont.load_default()
                self.small_font = ImageFont.load_default()
                
            logger.info("Fontes carregadas com sucesso")
            
        except Exception as e:
            logger.warning(f"Erro ao carregar fontes: {e}. Usando fonte padrão.")
            # Usar fontes padrão
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.data_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
    
    def generate_basic_cnh(self, cnh_request):
        """
        Gera CNH usando template oficial com coordenadas precisas.
        
        Args:
            cnh_request: Objeto CNHRequest com dados
            
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
            except Exception as e:
                logger.error(f"Erro ao aplicar coordenadas: {str(e)}")
                # Fallback: desenhar apenas o nome no centro para testar
                draw.text((100, 200), cnh_request.nome_completo or "TESTE", fill=(0, 0, 0))
            
            # Gerar nome único para arquivo
            filename = self._generate_filename(cnh_request)
            filepath = os.path.join(self.OUTPUT_DIR, filename)
            
            # Salvar imagem
            image.save(filepath, 'PNG', quality=95)
            
            logger.info(f"CNH gerada com sucesso - Arquivo: {filepath}")
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
                    font = self._get_font(font_config["size"])
                    
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
            
            # Número da habilitação (rotacionado)
            numero_habilitacao = cnh_request.numero_registro or f"{cnh_request.id:011d}"
            draw_field_if_exists("numero_habilitacao", numero_habilitacao, rotated=True, rotation=270)
            
            # Outros campos - só desenha se tiver coordenadas definidas
            
            # Primeira habilitação
            if cnh_request.primeira_habilitacao:
                primeira_hab = cnh_request.primeira_habilitacao.strftime("%d/%m/%Y")
                draw_field_if_exists("primeira_habilitacao", primeira_hab)
            
            # Data de nascimento
            if cnh_request.data_nascimento:
                data_nasc = cnh_request.data_nascimento.strftime("%d/%m/%Y")
                draw_field_if_exists("data_nascimento", data_nasc)
            
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
            
            # Nacionalidade
            nacionalidade = cnh_request.nacionalidade or "BRASILEIRA"
            draw_field_if_exists("nacionalidade", nacionalidade)
            
            # Filiação (nome da mãe)
            nome_mae = cnh_request.nome_mae or ""
            draw_field_if_exists("filiacao", nome_mae.upper())
                
            logger.info("Dados aplicados com sucesso usando coordenadas da matriz")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar dados com coordenadas: {str(e)}")
            raise e
    
    def _get_font(self, size):
        """
        Retorna fonte com tamanho especificado.
        
        Args:
            size: Tamanho da fonte
            
        Returns:
            ImageFont: Objeto de fonte
        """
        try:
            # Tentar usar Arial
            return ImageFont.truetype("arial.ttf", size)
        except:
            try:
                # Tentar fonte personalizada
                font_path = os.path.join(self.FONTS_DIR, "arial.ttf")
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except:
                pass
            # Fallback para fonte padrão
            return ImageFont.load_default()
    
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
            
            # Criar imagem temporária para o texto
            if rotation in [90, 270]:
                # Para rotações de 90° e 270°, invertemos largura e altura
                temp_img = Image.new('RGBA', (text_height + 20, text_width + 20), (255, 255, 255, 0))
            else:
                temp_img = Image.new('RGBA', (text_width + 20, text_height + 20), (255, 255, 255, 0))
            
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Desenhar texto na imagem temporária
            temp_draw.text((10, 10), text, font=font, fill=color)
            
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
                # Texto vertical (de cima para baixo)
                paste_x = int(x - temp_img.width // 2)
                paste_y = int(y - temp_img.height)
            else:
                # Texto horizontal
                paste_x = int(x)
                paste_y = int(y)
            
            # Colar usando a própria imagem como máscara para transparência
            draw._image.paste(temp_img, (paste_x, paste_y), temp_img)
            
            logger.debug(f"Texto rotacionado '{text}' desenhado em ({paste_x}, {paste_y}) com rotação {rotation}°")
            
        except Exception as e:
            logger.error(f"Erro ao desenhar texto rotacionado: {str(e)}")
            # Fallback: desenhar texto normal se a rotação falhar
            draw.text(position, text, font=font, fill=color)
    
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
        
        # Nacionalidade
        nacionalidade = cnh_request.nacionalidade or "BRASILEIRO"
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
        
        # Coluna 2 - Datas e local
        if cnh_request.data_nascimento:
            data_nasc_formatada = cnh_request.data_nascimento.strftime("%d/%m/%Y")
            idade = cnh_request.get_idade()
        else:
            data_nasc_formatada = "NÃO INFORMADA"
            idade = 0
        
        self._draw_modern_field(draw, "DATA NASCIMENTO", data_nasc_formatada, 
                               col2_x, start_y, 100)
        
        self._draw_modern_field(draw, "IDADE", f"{idade} anos" if idade > 0 else "NÃO CALC.", 
                               col2_x, start_y + line_height, 80)
        
        # Local de nascimento
        local_nasc = cnh_request.local_nascimento or "NÃO INFORMADO"
        uf_nasc = cnh_request.uf_nascimento or ""
        local_completo = f"{local_nasc}/{uf_nasc}" if uf_nasc else local_nasc
        self._draw_modern_field(draw, "LOCAL NASCIMENTO", local_completo.upper(), 
                               col2_x, start_y + line_height * 2, 150)
        
        # Primeira habilitação
        if cnh_request.primeira_habilitacao:
            primeira_hab = cnh_request.primeira_habilitacao.strftime("%d/%m/%Y")
        else:
            primeira_hab = "NÃO INFORMADA"
        self._draw_modern_field(draw, "1ª HABILITAÇÃO", primeira_hab, 
                               col2_x, start_y + line_height * 3, 120)
        
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
    
    def _generate_filename(self, cnh_request):
        """
        Gera nome único para arquivo da CNH.
        
        Args:
            cnh_request: Objeto CNHRequest
            
        Returns:
            str: Nome do arquivo
        """
        # Usar ID da CNH + timestamp para garantir unicidade
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cnh_{cnh_request.id:06d}_{timestamp}.png"
        return filename
    
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

# ==================== FUNÇÃO PRINCIPAL ====================

def gerar_cnh_basica(cnh_request):
    """
    Função principal para gerar CNH básica.
    
    Args:
        cnh_request: Objeto CNHRequest
        
    Returns:
        tuple: (success: bool, image_path: str, error_message: str)
    """
    try:
        generator = CNHImageGenerator()
        
        # Marcar como processando
        cnh_request.marcar_como_processando()
        
        # Gerar imagem
        image_path = generator.generate_basic_cnh(cnh_request)
        
        # Validar imagem gerada
        if not generator.validate_image(image_path):
            error_msg = "Imagem gerada é inválida"
            cnh_request.marcar_como_falha(error_msg)
            return False, None, error_msg
        
        # Gerar thumbnail (opcional) - DESABILITADO para evitar imagens duplicadas
        # generator.generate_thumbnail(image_path)
        
        # Marcar como completa
        cnh_request.marcar_como_completa(image_path)
        
        logger.info(f"CNH gerada com sucesso - ID: {cnh_request.id}, Arquivo: {image_path}")
        return True, image_path, ""
        
    except Exception as e:
        error_msg = f"Erro na geração: {str(e)}"
        cnh_request.marcar_como_falha(error_msg)
        logger.error(f"Erro ao gerar CNH - ID: {cnh_request.id}, Erro: {error_msg}")
        return False, None, error_msg 