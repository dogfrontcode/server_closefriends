# -*- coding: utf-8 -*-
"""
🔲 QR Code Generator - Gerador de QR codes para CNHs

Sistema otimizado para geração de QR codes como imagens separadas:
- Organização por CPF 
- Integração com CNHPathManager
- QR codes salvos em uploads/cnh/{cpf}/qrcode/
"""

import qrcode
import os
import logging
from PIL import Image, ImageDraw
from typing import Optional
from services.path_manager import CNHPathManager

logger = logging.getLogger(__name__)

class CNHQRGenerator:
    """
    Gerador de QR codes para CNHs como imagens separadas.
    Salva QR codes na estrutura organizada: uploads/cnh/{cpf}/qrcode/{id}.png
    """
    
    # Configurações padrão
    QR_SIZE = (200, 200)  # Tamanho padrão do QR code
    QR_VERSION = 1        # Versão do QR code (1 = 21x21 modules)
    QR_BORDER = 4         # Borda ao redor do QR code
    QR_BOX_SIZE = 10      # Tamanho de cada módulo
    
    # Configurações de design moderno
    QR_FILL_COLOR = "#000000"     # Cor dos módulos (preto)
    QR_BACK_COLOR = "#FFFFFF"     # Cor do fundo (branco)
    QR_CORNER_RADIUS = 3          # Raio dos cantos arredondados
    QR_MODULE_STYLE = "rounded"   # Estilo dos módulos: "square", "rounded", "circle"
    
    def __init__(self):
        """Inicializa gerador de QR code."""
        logger.info("CNHQRGenerator inicializado")
    
    def _apply_rounded_corners(self, img: Image.Image, radius: int = None) -> Image.Image:
        """
        Aplica cantos arredondados na imagem do QR code.
        
        Args:
            img: Imagem do QR code
            radius: Raio dos cantos arredondados (padrão: usa self.QR_CORNER_RADIUS)
            
        Returns:
            Image.Image: Imagem com cantos arredondados
        """
        if radius is None:
            radius = self.QR_CORNER_RADIUS
            
        # Se radius for 0, retorna imagem original
        if radius <= 0:
            return img
            
        # Criar máscara com cantos arredondados
        mask = Image.new('L', img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        
        # Desenhar retângulo arredondado na máscara
        mask_draw.rounded_rectangle(
            [(0, 0), img.size], 
            radius=radius, 
            fill=255
        )
        
        # Converter imagem para RGBA se necessário
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Aplicar máscara na imagem
        img.putalpha(mask)
        
        # Criar fundo branco (converter cor hex para RGB se necessário)
        back_color = self.QR_BACK_COLOR
        if isinstance(back_color, str) and back_color.startswith('#'):
            # Converter hex para RGB
            back_color = tuple(int(back_color[i:i+2], 16) for i in (1, 3, 5))
        elif isinstance(back_color, str):
            # Se for nome da cor, usar branco como padrão
            back_color = (255, 255, 255)
        
        background = Image.new('RGB', img.size, back_color)
        background.paste(img, (0, 0), img)
        
        return background
    
    def _create_modern_qr_image(self, qr_data: str) -> Image.Image:
        """
        Cria QR code com design moderno melhorado.
        
        Args:
            qr_data: Dados para o QR code
            
        Returns:
            Image.Image: Imagem do QR code com design moderno
        """
        # Configurar QR code com melhor correção de erro
        qr = qrcode.QRCode(
            version=self.QR_VERSION,
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Melhor correção
            box_size=self.QR_BOX_SIZE,
            border=self.QR_BORDER
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Gerar imagem base
        qr_img = qr.make_image(
            fill_color=self.QR_FILL_COLOR, 
            back_color=self.QR_BACK_COLOR
        )
        
        # Aplicar cantos arredondados se especificado
        if self.QR_MODULE_STYLE == "rounded" and self.QR_CORNER_RADIUS > 0:
            qr_img = self._apply_rounded_corners(qr_img)
        
        return qr_img
    
    def generate_qr_centralizado_cnh(self, cnh_request, url: str, 
                                   estilo: str = "premium", 
                                   tamanho_qr: int = 440) -> str:
        """
        Gera QR code centralizado em base branca com dimensões da CNH (673x496).
        
        Args:
            cnh_request: Objeto CNHRequest
            url: URL que o QR code vai apontar
            estilo: Estilo do QR ("tradicional", "moderno", "premium", "customizado", "compacto", "resistente")
            tamanho_qr: Tamanho do QR code em pixels
            
        Returns:
            str: Caminho absoluto da imagem QR code centralizada gerada
        """
        try:
            logger.info(f"Gerando QR code centralizado estilo {estilo} para CNH ID: {cnh_request.id}")
            
            # Dimensões da CNH
            CNH_WIDTH = 673
            CNH_HEIGHT = 496
            
            # Criar paths usando CNHPathManager existente
            paths = CNHPathManager.create_cnh_paths(cnh_request)
            CNHPathManager.ensure_directories(paths)
            
            # Gerar QR code baseado no estilo
            if estilo == "tradicional":
                qr_img = self._create_qr_tradicional(url)
            elif estilo == "moderno":
                qr_img = self._create_qr_moderno(url)
            elif estilo == "premium":
                qr_img = self._create_qr_premium_interno(url)
            elif estilo == "customizado":
                qr_img = self._create_qr_customizado(url)
            elif estilo == "compacto":
                qr_img = self._create_qr_compacto(url)
            elif estilo == "resistente":
                qr_img = self._create_qr_resistente(url)
            else:
                raise ValueError(f"Estilo '{estilo}' não reconhecido")
            
            # Redimensionar QR code para 440x443 (como solicitado)
            if tamanho_qr == 440:
                qr_img = qr_img.resize((440, 443), Image.Resampling.LANCZOS)
            else:
                qr_img = qr_img.resize((tamanho_qr, tamanho_qr), Image.Resampling.LANCZOS)
            
            # Rotacionar QR code 90 graus para a esquerda (para corrigir visualização)
            qr_img = qr_img.rotate(90, expand=True)
            
            # Criar base branca com dimensões da CNH
            base_cnh = Image.new('RGB', (CNH_WIDTH, CNH_HEIGHT), 'white')
            
            # Calcular posição central considerando a rotação
            # Após rotação de 90°, largura e altura se invertem
            if tamanho_qr == 440:
                # Original: 440x443, Após rotação: 443x440
                qr_width = 443
                qr_height = 440
            else:
                # Para outros tamanhos (quadrados), não muda
                qr_width = tamanho_qr
                qr_height = tamanho_qr
            
            x_center = (CNH_WIDTH - qr_width) // 2
            y_center = (CNH_HEIGHT - qr_height) // 2
            
            # Colar QR code no centro
            base_cnh.paste(qr_img, (x_center, y_center))
            
            # Salvar na pasta qrcode com nome simples (igual aos outros arquivos)
            base_cnh.save(paths.qrcode_path, 'PNG', quality=100)
            qr_centralizado_path = paths.qrcode_path
            
            logger.info(f"QR code centralizado salvo: {qr_centralizado_path}")
            return qr_centralizado_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code centralizado: {str(e)}")
            raise e
    
    def _create_qr_tradicional(self, url):
        """Cria QR code tradicional"""
        import qrcode
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")
    
    def _create_qr_moderno(self, url):
        """Cria QR code moderno com cantos arredondados"""
        import qrcode
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
        return self._apply_rounded_corners(qr_img, radius=6)
    
    def _create_qr_premium_interno(self, url):
        """Cria QR code premium (alta qualidade)"""
        import qrcode
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
        return self._apply_rounded_corners(qr_img, radius=8)
    
    def _create_qr_customizado(self, url):
        """Cria QR code com cores customizadas"""
        import qrcode
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#1a365d", back_color="#f7fafc")
        return self._apply_rounded_corners(qr_img, radius=4)
    
    def _create_qr_compacto(self, url):
        """Cria QR code compacto"""
        import qrcode
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")
    
    def _create_qr_resistente(self, url):
        """Cria QR code resistente (máxima correção)"""
        import qrcode
        qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        return qr.make_image(fill_color="#2d3748", back_color="#ffffff")
    
    def generate_qr_premium_style(self, cnh_request, url: str, 
                                custom_size: Optional[tuple] = None) -> str:
        """
        Gera QR code com estilo premium otimizado para CNHs.
        Usa configurações que se assemelham mais a documentos oficiais.
        
        Args:
            cnh_request: Objeto CNHRequest
            url: URL que o QR code vai apontar
            custom_size: Tamanho customizado (width, height)
            
        Returns:
            str: Caminho absoluto da imagem QR code gerada
        """
        try:
            logger.info(f"Gerando QR code premium para CNH ID: {cnh_request.id}")
            
            # Criar paths usando CNHPathManager existente
            paths = CNHPathManager.create_cnh_paths(cnh_request)
            CNHPathManager.ensure_directories(paths)
            
            # Configurações premium para documentos oficiais
            qr = qrcode.QRCode(
                version=1,  # Tamanho compacto
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta correção
                box_size=12,  # Módulos um pouco maiores
                border=2      # Borda mais fina
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Gerar imagem base
            qr_img = qr.make_image(
                fill_color="#000000",  # Preto puro
                back_color="#FFFFFF"   # Branco puro
            )
            
            # Aplicar cantos levemente arredondados (mais sutil)
            qr_img = self._apply_rounded_corners(qr_img, radius=8)
            
            # Redimensionar para tamanho especificado
            target_size = custom_size or (180, 180)  # Tamanho otimizado para CNH
            qr_img = qr_img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Salvar com alta qualidade
            qr_img.save(paths.qrcode_path, 'PNG', quality=100, optimize=True, dpi=(300, 300))
            
            logger.info(f"QR code premium salvo: {paths.qrcode_path}")
            return paths.qrcode_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code premium: {str(e)}")
            raise e
    
    def generate_qr_image_with_style(self, cnh_request, url: str, 
                                   custom_size: Optional[tuple] = None,
                                   fill_color: str = None,
                                   back_color: str = None,
                                   corner_radius: int = None,
                                   high_quality: bool = True) -> str:
        """
        Gera QR code com opções de estilo customizáveis.
        
        Args:
            cnh_request: Objeto CNHRequest
            url: URL que o QR code vai apontar
            custom_size: Tamanho customizado (width, height)
            fill_color: Cor dos módulos (hex) - padrão: usar QR_FILL_COLOR
            back_color: Cor do fundo (hex) - padrão: usar QR_BACK_COLOR
            corner_radius: Raio dos cantos - padrão: usar QR_CORNER_RADIUS
            high_quality: Se deve usar alta qualidade (melhor correção de erro)
            
        Returns:
            str: Caminho absoluto da imagem QR code gerada
        """
        try:
            logger.info(f"Gerando QR code estilizado para CNH ID: {cnh_request.id}")
            
            # Criar paths usando CNHPathManager existente
            paths = CNHPathManager.create_cnh_paths(cnh_request)
            CNHPathManager.ensure_directories(paths)
            
            # Aplicar cores customizadas temporariamente
            original_fill = self.QR_FILL_COLOR
            original_back = self.QR_BACK_COLOR
            original_radius = self.QR_CORNER_RADIUS
            
            if fill_color:
                self.QR_FILL_COLOR = fill_color
            if back_color:
                self.QR_BACK_COLOR = back_color
            if corner_radius is not None:
                self.QR_CORNER_RADIUS = corner_radius
            
            # Configurar QR code
            error_correction = qrcode.constants.ERROR_CORRECT_H if high_quality else qrcode.constants.ERROR_CORRECT_M
            
            qr = qrcode.QRCode(
                version=self.QR_VERSION,
                error_correction=error_correction,
                box_size=self.QR_BOX_SIZE,
                border=self.QR_BORDER
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Gerar imagem base
            qr_img = qr.make_image(
                fill_color=self.QR_FILL_COLOR, 
                back_color=self.QR_BACK_COLOR
            )
            
            # Aplicar cantos arredondados
            if self.QR_CORNER_RADIUS > 0:
                qr_img = self._apply_rounded_corners(qr_img)
            
            # Redimensionar para tamanho especificado
            target_size = custom_size or self.QR_SIZE
            qr_img = qr_img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Salvar na pasta qrcode
            qr_img.save(paths.qrcode_path, 'PNG', quality=95, optimize=True)
            
            # Restaurar configurações originais
            self.QR_FILL_COLOR = original_fill
            self.QR_BACK_COLOR = original_back
            self.QR_CORNER_RADIUS = original_radius
            
            logger.info(f"QR code estilizado salvo: {paths.qrcode_path}")
            return paths.qrcode_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code estilizado: {str(e)}")
            raise e
    
    def generate_qr_image(self, cnh_request, url: str, custom_size: Optional[tuple] = None) -> str:
        """
        Gera QR code como imagem PNG separada.
        
        Args:
            cnh_request: Objeto CNHRequest
            url: URL que o QR code vai apontar
            custom_size: Tamanho customizado (width, height), opcional
            
        Returns:
            str: Caminho absoluto da imagem QR code gerada
            
        Raises:
            Exception: Se houver erro na geração
        """
        try:
            logger.info(f"Gerando QR code para CNH ID: {cnh_request.id}")
            logger.info(f"URL do QR code: {url}")
            
            # Criar paths usando CNHPathManager existente
            paths = CNHPathManager.create_cnh_paths(cnh_request)
            CNHPathManager.ensure_directories(paths)
            
            # Gerar QR code com design moderno
            qr_img = self._create_modern_qr_image(url)
            
            # Redimensionar para tamanho especificado
            target_size = custom_size or self.QR_SIZE
            qr_img = qr_img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Salvar na pasta qrcode
            qr_img.save(paths.qrcode_path, 'PNG', quality=95)
            
            logger.info(f"QR code salvo com sucesso: {paths.qrcode_path}")
            logger.info(f"Tamanho da imagem: {target_size}")
            
            return paths.qrcode_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code para CNH {cnh_request.id}: {str(e)}")
            raise e
    
    def generate_qr_for_cnh_url(self, cnh_request, base_url: str) -> str:
        """
        Gera QR code que aponta para URL da própria CNH (frente).
        
        Args:
            cnh_request: Objeto CNHRequest  
            base_url: URL base do site (ex: https://seusite.com)
            
        Returns:
            str: Caminho absoluto da imagem QR code gerada
        """
        try:
            # Gerar URL da CNH usando nova estrutura user_id + cpf
            user_folder_name = CNHPathManager.get_user_folder_name(cnh_request.user_id)
            cpf_clean = CNHPathManager.get_cpf_clean(cnh_request.cpf)
            cnh_url = f"{base_url}/static/uploads/cnh/{user_folder_name}/{cpf_clean}/front/{cnh_request.id}.png"
            
            logger.info(f"Gerando QR code para URL da CNH: {cnh_url}")
            
            return self.generate_qr_image(cnh_request, cnh_url)
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code para URL da CNH {cnh_request.id}: {str(e)}")
            raise e
    
    def generate_qr_for_validation_url(self, cnh_request, base_url: str) -> str:
        """
        Gera QR code que aponta para página de validação da CNH.
        
        Args:
            cnh_request: Objeto CNHRequest
            base_url: URL base do site
            
        Returns:
            str: Caminho absoluto da imagem QR code gerada
        """
        try:
            # Gerar URL de validação (para implementação futura)
            validation_url = f"{base_url}/validar-cnh/{cnh_request.id}"
            
            # Se houver senha CNH, adicionar como parâmetro
            if hasattr(cnh_request, 'cnh_password') and cnh_request.cnh_password:
                validation_url += f"?senha={cnh_request.cnh_password}"
            
            logger.info(f"Gerando QR code para validação: {validation_url}")
            
            return self.generate_qr_image(cnh_request, validation_url)
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code de validação para CNH {cnh_request.id}: {str(e)}")
            raise e
    
    def generate_qr_for_custom_url(self, cnh_request, custom_url: str) -> str:
        """
        Gera QR code para URL customizada.
        
        Args:
            cnh_request: Objeto CNHRequest
            custom_url: URL customizada
            
        Returns:
            str: Caminho absoluto da imagem QR code gerada
        """
        try:
            logger.info(f"Gerando QR code para URL customizada: {custom_url}")
            
            return self.generate_qr_image(cnh_request, custom_url)
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code customizado para CNH {cnh_request.id}: {str(e)}")
            raise e
    
    def validate_qr_image(self, qr_path: str) -> bool:
        """
        Valida se a imagem QR code foi gerada corretamente.
        
        Args:
            qr_path: Caminho da imagem QR code
            
        Returns:
            bool: True se válida, False caso contrário
        """
        try:
            if not os.path.exists(qr_path):
                logger.error(f"Arquivo QR code não existe: {qr_path}")
                return False
            
            # Verificar se arquivo não está vazio
            file_size = os.path.getsize(qr_path)
            if file_size == 0:
                logger.error(f"Arquivo QR code vazio: {qr_path}")
                return False
            
            # Tentar abrir imagem
            with Image.open(qr_path) as img:
                # Verificar dimensões mínimas
                width, height = img.size
                if width < 50 or height < 50:
                    logger.error(f"QR code muito pequeno: {img.size}")
                    return False
                
                # Verificar formato
                if img.format != 'PNG':
                    logger.error(f"Formato QR code inválido: {img.format}")
                    return False
            
            logger.info(f"QR code válido: {qr_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar QR code: {str(e)}")
            return False
    
    def get_qr_relative_path(self, cnh_request) -> str:
        """
        Retorna path relativo do QR code para uso no frontend.
        
        Args:
            cnh_request: Objeto CNHRequest
            
        Returns:
            str: Path relativo do QR code
        """
        paths = CNHPathManager.create_cnh_paths(cnh_request)
        return paths.qrcode_relative
    
    def delete_qr_image(self, cnh_request) -> bool:
        """
        Remove imagem QR code específica.
        
        Args:
            cnh_request: Objeto CNHRequest
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            paths = CNHPathManager.create_cnh_paths(cnh_request)
            
            if os.path.exists(paths.qrcode_path):
                os.remove(paths.qrcode_path)
                logger.info(f"QR code removido: {paths.qrcode_path}")
                return True
            else:
                logger.warning(f"QR code não existe para remoção: {paths.qrcode_path}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover QR code: {str(e)}")
            return False

# ==================== FUNÇÃO UTILITÁRIA ====================

def gerar_qr_para_cnh(cnh_request, base_url: str, tipo: str = "cnh_url", estilo_moderno: bool = True, estilo_premium: bool = False) -> tuple:
    """
    Função utilitária para gerar QR code para CNH.
    
    Args:
        cnh_request: Objeto CNHRequest
        base_url: URL base do site
        tipo: Tipo de QR code ("cnh_url", "validation", "custom")
        estilo_moderno: Se deve usar design moderno com cantos arredondados
        estilo_premium: Se deve usar estilo premium otimizado para documentos
        
    Returns:
        tuple: (success: bool, qr_path: str, error_message: str)
    """
    try:
        generator = CNHQRGenerator()
        
        # Escolher método baseado no estilo (premium tem prioridade)
        if estilo_premium:
            # Usar estilo premium (mais parecido com documentos oficiais)
            if tipo == "cnh_url":
                # Gerar URL da CNH
                user_folder_name = CNHPathManager.get_user_folder_name(cnh_request.user_id)
                cpf_clean = CNHPathManager.get_cpf_clean(cnh_request.cpf)
                cnh_url = f"{base_url}/static/uploads/cnh/{user_folder_name}/{cpf_clean}/front/{cnh_request.id}.png"
                qr_path = generator.generate_qr_premium_style(cnh_request, cnh_url)
            elif tipo == "validation":
                # Gerar URL de validação
                validation_url = f"{base_url}/validar-cnh/{cnh_request.id}"
                if hasattr(cnh_request, 'cnh_password') and cnh_request.cnh_password:
                    validation_url += f"?senha={cnh_request.cnh_password}"
                qr_path = generator.generate_qr_premium_style(cnh_request, validation_url)
            else:
                raise ValueError(f"Tipo de QR code inválido: {tipo}")
        elif estilo_moderno:
            # Usar método com estilo moderno
            if tipo == "cnh_url":
                # Gerar URL da CNH
                user_folder_name = CNHPathManager.get_user_folder_name(cnh_request.user_id)
                cpf_clean = CNHPathManager.get_cpf_clean(cnh_request.cpf)
                cnh_url = f"{base_url}/static/uploads/cnh/{user_folder_name}/{cpf_clean}/front/{cnh_request.id}.png"
                qr_path = generator.generate_qr_image_with_style(
                    cnh_request, 
                    cnh_url,
                    corner_radius=5,  # Cantos mais arredondados
                    high_quality=True
                )
            elif tipo == "validation":
                # Gerar URL de validação
                validation_url = f"{base_url}/validar-cnh/{cnh_request.id}"
                if hasattr(cnh_request, 'cnh_password') and cnh_request.cnh_password:
                    validation_url += f"?senha={cnh_request.cnh_password}"
                qr_path = generator.generate_qr_image_with_style(
                    cnh_request, 
                    validation_url,
                    corner_radius=5,
                    high_quality=True
                )
            else:
                raise ValueError(f"Tipo de QR code inválido: {tipo}")
        else:
            # Usar método tradicional
            if tipo == "cnh_url":
                qr_path = generator.generate_qr_for_cnh_url(cnh_request, base_url)
            elif tipo == "validation":
                qr_path = generator.generate_qr_for_validation_url(cnh_request, base_url)
            else:
                raise ValueError(f"Tipo de QR code inválido: {tipo}")
        
        # Validar QR code gerado
        if not generator.validate_qr_image(qr_path):
            return False, None, "QR code gerado é inválido"
        
        if estilo_premium:
            style_msg = "premium"
        elif estilo_moderno:
            style_msg = "moderno"
        else:
            style_msg = "tradicional"
            
        logger.info(f"QR code {style_msg} gerado com sucesso para CNH {cnh_request.id}: {qr_path}")
        return True, qr_path, ""
        
    except Exception as e:
        error_msg = f"Erro ao gerar QR code: {str(e)}"
        logger.error(f"Erro na função gerar_qr_para_cnh: {error_msg}")
        return False, None, error_msg

def gerar_qr_centralizado_para_cnh(cnh_request, base_url: str, estilo: str = "premium", tamanho_qr: int = 440) -> tuple:
    """
    Função utilitária para gerar QR code centralizado em base branca formato CNH.
    
    Args:
        cnh_request: Objeto CNHRequest
        base_url: URL base do site
        estilo: Estilo do QR ("tradicional", "moderno", "premium", "customizado", "compacto", "resistente")
        tamanho_qr: Tamanho do QR code em pixels (padrão: 440 - gera 440x443)
        
    Returns:
        tuple: (success: bool, qr_path: str, error_message: str)
    """
    try:
        generator = CNHQRGenerator()
        
        # Gerar URL da CNH
        user_folder_name = CNHPathManager.get_user_folder_name(cnh_request.user_id)
        cpf_clean = CNHPathManager.get_cpf_clean(cnh_request.cpf)
        cnh_url = f"{base_url}/static/uploads/cnh/{user_folder_name}/{cpf_clean}/front/{cnh_request.id}.png"
        
        # Gerar QR code centralizado
        qr_path = generator.generate_qr_centralizado_cnh(cnh_request, cnh_url, estilo, tamanho_qr)
        
        # Validar QR code gerado
        if not generator.validate_qr_image(qr_path):
            return False, None, "QR code centralizado gerado é inválido"
        
        logger.info(f"QR code centralizado {estilo} gerado com sucesso para CNH {cnh_request.id}: {qr_path}")
        return True, qr_path, ""
        
    except Exception as e:
        error_msg = f"Erro ao gerar QR code centralizado: {str(e)}"
        logger.error(f"Erro na função gerar_qr_centralizado_para_cnh: {error_msg}")
        return False, None, error_msg