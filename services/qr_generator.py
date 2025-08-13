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
from PIL import Image
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
    
    def __init__(self):
        """Inicializa gerador de QR code."""
        logger.info("CNHQRGenerator inicializado")
    
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
            
            # Configurar QR code
            qr = qrcode.QRCode(
                version=self.QR_VERSION,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=self.QR_BOX_SIZE,
                border=self.QR_BORDER
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Gerar imagem do QR code
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
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

def gerar_qr_para_cnh(cnh_request, base_url: str, tipo: str = "cnh_url") -> tuple:
    """
    Função utilitária para gerar QR code para CNH.
    
    Args:
        cnh_request: Objeto CNHRequest
        base_url: URL base do site
        tipo: Tipo de QR code ("cnh_url", "validation", "custom")
        
    Returns:
        tuple: (success: bool, qr_path: str, error_message: str)
    """
    try:
        generator = CNHQRGenerator()
        
        if tipo == "cnh_url":
            qr_path = generator.generate_qr_for_cnh_url(cnh_request, base_url)
        elif tipo == "validation":
            qr_path = generator.generate_qr_for_validation_url(cnh_request, base_url)
        else:
            raise ValueError(f"Tipo de QR code inválido: {tipo}")
        
        # Validar QR code gerado
        if not generator.validate_qr_image(qr_path):
            return False, None, "QR code gerado é inválido"
        
        logger.info(f"QR code gerado com sucesso para CNH {cnh_request.id}: {qr_path}")
        return True, qr_path, ""
        
    except Exception as e:
        error_msg = f"Erro ao gerar QR code: {str(e)}"
        logger.error(f"Erro na função gerar_qr_para_cnh: {error_msg}")
        return False, None, error_msg