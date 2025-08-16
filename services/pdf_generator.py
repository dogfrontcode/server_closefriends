# -*- coding: utf-8 -*-
"""
📄 PDF Generator - Geração de documentos CNH em PDF

Sistema simples para combinar as 4 imagens de CNH sobre uma base template.
"""

import os
import logging
from typing import Optional, Tuple
from PIL import Image
from services.path_manager import CNHPathManager

# Importar coordenadas do arquivo específico
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'static', 'cnh_matriz'))
from pdf_coordinates import get_pdf_coordinates

logger = logging.getLogger(__name__)

class CNHPDFGenerator:
    """
    Gerador simples de PDFs para documentos CNH.
    Usa uma imagem base e empilha as 4 imagens CNH.
    """
    
    # Configurações (agora vêm do arquivo de coordenadas)
    def __init__(self, layout_name="stacked"):
        """Inicializa o gerador com layout específico."""
        self.layout = get_pdf_coordinates(layout_name)
        self.BASE_TEMPLATE = self.layout["base_template"]
        self.SPACING = self.layout.get("spacing_between_images", 5)
        logger.debug(f"PDF Generator inicializado com layout: {layout_name}")
    

    
    def _validate_image(self, image_path: str) -> bool:
        """Valida se uma imagem existe."""
        if not os.path.exists(image_path):
            logger.warning(f"Imagem não encontrada: {image_path}")
            return False
        return True
    

    
    def generate_cnh_pdf(self, cnh_request, output_path: Optional[str] = None) -> str:
        """
        Gera PDF simples com as 4 imagens empilhadas na base.
        
        Args:
            cnh_request: Objeto CNHRequest
            output_path: Caminho de saída (opcional)
            
        Returns:
            str: Caminho do arquivo gerado
        """
        try:
            logger.info(f"🚀 Iniciando geração de PDF CNH - ID: {cnh_request.id}")
            
            # Obter paths
            paths = CNHPathManager.create_cnh_paths(cnh_request)
            
            # Definir saída
            if output_path:
                final_output = output_path
            else:
                # Primeiro salvar como imagem, depois converter para PDF
                image_output = paths.pdf_path.replace('.pdf', '.png')
                final_output = paths.pdf_path
            
            # Garantir diretório
            os.makedirs(os.path.dirname(final_output), exist_ok=True)
            
            # Verificar imagens
            image_paths = [paths.front_path, paths.back_path, paths.back2_path, paths.qrcode_path]
            missing = [p for p in image_paths if not self._validate_image(p)]
            
            if missing:
                raise Exception(f"Imagens não encontradas: {missing}")
            
            # Criar imagem combinada
            combined_image_path = self._create_combined_image(image_paths, image_output)
            
            # Converter para PDF
            pdf_path = self._convert_to_pdf(combined_image_path, final_output)
            
            logger.info(f"✅ PDF gerado: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            error_msg = f"Erro ao gerar PDF: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _create_combined_image(self, image_paths: list, output_path: str) -> str:
        """
        Cria imagem combinada usando base + 4 imagens empilhadas.
        
        Args:
            image_paths: Lista com [front, back, back2, qrcode] paths
            output_path: Onde salvar a imagem combinada
            
        Returns:
            str: Caminho da imagem criada
        """
        try:
            # Carregar imagem base
            base_path = os.path.join(os.path.dirname(__file__), '..', self.BASE_TEMPLATE)
            
            if not os.path.exists(base_path):
                raise Exception(f"Template base não encontrado: {base_path}")
            
            base_img = Image.open(base_path).convert('RGB')
            logger.info(f"Template base carregado: {base_img.size}")
            
            # Obter configurações do layout
            start_x = self.layout.get("start_x", 50)
            start_y = self.layout.get("start_y", 50)
            target_width = self.layout.get("target_width", 800)
            target_height = self.layout.get("target_height", 600)
            
            # Verificar se tem posições específicas ou usar empilhamento dinâmico
            use_specific_positions = "positions" in self.layout
            current_y = start_y  # Sempre inicializar current_y
            
            if use_specific_positions:
                positions = self.layout["positions"]
                logger.info("Usando posições específicas do layout")
            else:
                logger.info("Usando empilhamento dinâmico")
            
            # Carregar e empilhar cada imagem
            image_names = ['front', 'back', 'back2', 'qrcode']
            
            for i, img_path in enumerate(image_paths):
                if self._validate_image(img_path):
                    # Abrir imagem
                    img = Image.open(img_path).convert('RGB')
                    
                    # Redimensionar mantendo proporção
                    if not self.layout.get("preserve_original_size", False):
                        ratio = min(target_width / img.width, target_height / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                    else:
                        img_resized = img
                        new_size = img.size
                    
                    # Determinar posição
                    if use_specific_positions:
                        pos_x, pos_y = positions.get(image_names[i], (start_x, current_y))
                    else:
                        pos_x, pos_y = start_x, current_y
                        current_y += img_resized.height + self.SPACING
                    
                    # Colar na posição determinada
                    base_img.paste(img_resized, (pos_x, pos_y))
                    logger.info(f"✅ {image_names[i]} colada em ({pos_x}, {pos_y}) - Tamanho: {new_size}")
                    
                else:
                    logger.warning(f"⚠️ Imagem {image_names[i]} não encontrada: {img_path}")
            
            # Salvar imagem combinada
            base_img.save(output_path, 'PNG', quality=95)
            logger.info(f"📷 Imagem combinada salva: {output_path}")
            
            return output_path
            
        except Exception as e:
            error_msg = f"Erro ao criar imagem combinada: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _convert_to_pdf(self, image_path: str, pdf_path: str) -> str:
        """
        Converte imagem para PDF.
        
        Args:
            image_path: Caminho da imagem
            pdf_path: Caminho de saída do PDF
            
        Returns:
            str: Caminho do PDF criado
        """
        try:
            # Abrir imagem
            img = Image.open(image_path)
            
            # Converter para PDF
            img.save(pdf_path, 'PDF', quality=95)
            logger.info(f"📄 PDF criado: {pdf_path}")
            
            return pdf_path
            
        except Exception as e:
            error_msg = f"Erro ao converter para PDF: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)


# ==================== FUNÇÃO PRINCIPAL ====================

def gerar_cnh_pdf(cnh_request, output_path: Optional[str] = None, layout: str = "stacked") -> Tuple[bool, str, str]:
    """
    Função principal para gerar PDF de CNH.
    
    Args:
        cnh_request: Objeto CNHRequest
        output_path: Caminho específico (opcional)
        layout: Layout a usar ("stacked", "grid", "template_based")
        
    Returns:
        tuple: (success: bool, pdf_path: str, error_message: str)
    """
    try:
        generator = CNHPDFGenerator(layout)
        
        logger.info(f"🚀 GERANDO PDF CNH - ID: {cnh_request.id} - Layout: {layout}")
        
        # Gerar PDF
        pdf_path = generator.generate_cnh_pdf(cnh_request, output_path)
        
        # Validar
        if not os.path.exists(pdf_path):
            return False, "", "PDF não foi criado"
        
        logger.info(f"✅ PDF criado com sucesso - ID: {cnh_request.id}")
        return True, pdf_path, ""
        
    except Exception as e:
        error_msg = f"Erro: {str(e)}"
        logger.error(f"❌ Erro PDF CNH {cnh_request.id}: {error_msg}")
        return False, "", error_msg
