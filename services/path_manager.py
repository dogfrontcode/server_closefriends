# -*- coding: utf-8 -*-
"""
🗂️ Path Manager - Gerenciamento centralizado de paths para CNHs

Sistema otimizado para organização de arquivos CNH por CPF.
Facilita edição/regeneração de imagens e mantém estrutura limpa.
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CNHPaths:
    """Estrutura para paths de uma CNH."""
    cpf_folder: str
    front_path: str
    back_path: str
    qrcode_path: str
    front_relative: str
    back_relative: str
    qrcode_relative: str

class CNHPathManager:
    """
    Gerenciador centralizado de paths para CNHs.
    Organiza arquivos por CPF para facilitar edição e administração.
    """
    
    BASE_DIR = "static/uploads/cnh"
    ALLOWED_TYPES = ["front", "back", "qrcode"]
    
    @classmethod
    def get_cpf_clean(cls, cpf: str) -> str:
        """
        Limpa CPF removendo pontos, traços e espaços.
        
        Args:
            cpf: CPF formatado ou não
            
        Returns:
            str: CPF limpo (apenas números)
        """
        if not cpf:
            return "unknown"
        return ''.join(filter(str.isdigit, cpf))
    
    @classmethod
    def create_cnh_paths(cls, cnh_request, filename: Optional[str] = None) -> CNHPaths:
        """
        Cria estrutura completa de paths para uma CNH.
        
        Args:
            cnh_request: Objeto CNHRequest
            filename: Nome do arquivo (default: {id}.png)
            
        Returns:
            CNHPaths: Estrutura com todos os paths
        """
        if not filename:
            filename = f"{cnh_request.id}.png"
        
        cpf_clean = cls.get_cpf_clean(cnh_request.cpf)
        cpf_folder = os.path.join(cls.BASE_DIR, cpf_clean)
        
        # Criar paths absolutos
        front_path = os.path.join(cpf_folder, "front", filename)
        back_path = os.path.join(cpf_folder, "back", filename)
        qrcode_path = os.path.join(cpf_folder, "qrcode", filename)
        
        # Criar paths relativos
        front_relative = f"{cls.BASE_DIR}/{cpf_clean}/front/{filename}"
        back_relative = f"{cls.BASE_DIR}/{cpf_clean}/back/{filename}"
        qrcode_relative = f"{cls.BASE_DIR}/{cpf_clean}/qrcode/{filename}"
        
        return CNHPaths(
            cpf_folder=cpf_folder,
            front_path=front_path,
            back_path=back_path,
            qrcode_path=qrcode_path,
            front_relative=front_relative,
            back_relative=back_relative,
            qrcode_relative=qrcode_relative
        )
    
    @classmethod
    def ensure_directories(cls, paths: CNHPaths) -> None:
        """
        Garante que todos os diretórios necessários existem.
        
        Args:
            paths: Estrutura CNHPaths
        """
        for file_type in cls.ALLOWED_TYPES:
            dir_path = os.path.join(paths.cpf_folder, file_type)
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Diretório garantido: {dir_path}")
    
    @classmethod
    def get_existing_paths(cls, cnh_request) -> Dict[str, Optional[str]]:
        """
        Retorna paths existentes para uma CNH.
        
        Args:
            cnh_request: Objeto CNHRequest
            
        Returns:
            dict: Paths que existem no sistema
        """
        paths = cls.create_cnh_paths(cnh_request)
        
        existing = {
            "front": paths.front_relative if os.path.exists(paths.front_path) else None,
            "back": paths.back_relative if os.path.exists(paths.back_path) else None,
            "qrcode": paths.qrcode_relative if os.path.exists(paths.qrcode_path) else None
        }
        
        return existing
    
    @classmethod
    def delete_cnh_files(cls, cnh_request) -> bool:
        """
        Remove todos os arquivos de uma CNH específica.
        Útil para regeneração completa.
        
        Args:
            cnh_request: Objeto CNHRequest
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            paths = cls.create_cnh_paths(cnh_request)
            
            files_removed = 0
            for file_path in [paths.front_path, paths.back_path, paths.qrcode_path]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    files_removed += 1
                    logger.info(f"Arquivo removido: {file_path}")
            
            logger.info(f"CNH {cnh_request.id}: {files_removed} arquivos removidos")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover arquivos CNH {cnh_request.id}: {str(e)}")
            return False
    
    @classmethod
    def delete_cpf_folder(cls, cpf: str) -> bool:
        """
        Remove toda a pasta de um CPF.
        Útil para exclusão completa ou regeneração total.
        
        Args:
            cpf: CPF formatado ou limpo
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            import shutil
            
            cpf_clean = cls.get_cpf_clean(cpf)
            cpf_folder = os.path.join(cls.BASE_DIR, cpf_clean)
            
            if os.path.exists(cpf_folder):
                shutil.rmtree(cpf_folder)
                logger.info(f"Pasta do CPF removida: {cpf_folder}")
                return True
            else:
                logger.warning(f"Pasta do CPF não existe: {cpf_folder}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover pasta do CPF {cpf}: {str(e)}")
            return False
    
    @classmethod
    def get_legacy_path_mapping(cls, old_path: str) -> Optional[str]:
        """
        Mapeia paths antigos para nova estrutura.
        Facilita migração e compatibilidade.
        
        Args:
            old_path: Path no formato antigo
            
        Returns:
            str: Path no novo formato ou None
        """
        if not old_path:
            return None
        
        # Mapear user_X/front/ID.png -> CPF/front/ID.png
        if '/user_' in old_path and '/front/' in old_path:
            return old_path.replace('/front/', '/back/') if '/front/' in old_path else None
        
        # Mapear estrutura antiga cnh_front_ -> nova estrutura
        if 'cnh_front_' in old_path:
            return old_path.replace('cnh_front_', 'cnh_back_')
        
        return None
