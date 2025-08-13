# -*- coding: utf-8 -*-
"""
🗂️ Path Manager - Gerenciamento centralizado de paths para CNHs

Sistema otimizado para organização de arquivos CNH por USER ID + CPF.
Nova estrutura: static/uploads/cnh/user_{id}/{cpf}/front|back|qrcode/
Evita conflitos entre usuários e facilita administração.
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CNHPaths:
    """Estrutura para paths de uma CNH com nova organização user_id + cpf."""
    user_folder: str      # pasta do usuário: user_123
    cpf_folder: str       # pasta do CPF: user_123/12345678900
    uploads_folder: str   # pasta uploads: user_123/12345678900/uploads
    front_path: str       # caminho completo frente
    back_path: str        # caminho completo verso
    qrcode_path: str      # caminho completo qr code
    front_relative: str   # path relativo frente
    back_relative: str    # path relativo verso
    qrcode_relative: str  # path relativo qr code

class CNHPathManager:
    """
    Gerenciador centralizado de paths para CNHs.
    NOVA ESTRUTURA: user_id + cpf para evitar conflitos entre usuários.
    
    Estrutura de pastas:
    static/uploads/cnh/
    ├── user_123/
    │   ├── 12345678900/    # CPF 1
    │   │   ├── front/
    │   │   ├── back/
    │   │   ├── qrcode/
    │   │   └── uploads/    # foto 3x4 e assinatura
    │   ├── 98765432100/    # CPF 2 (outro familiar)
    │   │   ├── front/
    │   │   ├── back/
    │   │   ├── qrcode/
    │   │   └── uploads/
    ├── user_456/
    │   ├── 12345678900/    # Mesmo CPF, usuário diferente
    │   │   ├── front/
    │   │   ├── back/
    │   │   ├── qrcode/
    │   │   └── uploads/
    """
    
    BASE_DIR = "static/uploads/cnh"
    ALLOWED_TYPES = ["front", "back", "qrcode", "uploads"]
    
    @classmethod
    def get_cpf_clean(cls, cpf: str) -> str:
        """
        Limpa CPF removendo pontos, traços e espaços.
        
        Args:
            cpf: CPF formatado ou não
            
        Returns:
            str: CPF limpo (apenas números) ou 'unknown'
        """
        if not cpf:
            return "unknown"
        return ''.join(filter(str.isdigit, cpf))
    
    @classmethod
    def get_user_folder_name(cls, user_id: int) -> str:
        """
        Gera nome da pasta do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            str: Nome da pasta (ex: user_123)
        """
        return f"user_{user_id}"
    
    @classmethod
    def create_cnh_paths(cls, cnh_request, filename: Optional[str] = None) -> CNHPaths:
        """
        Cria estrutura completa de paths para uma CNH com nova organização.
        
        Args:
            cnh_request: Objeto CNHRequest
            filename: Nome do arquivo (default: {id}.png)
            
        Returns:
            CNHPaths: Estrutura com todos os paths usando user_id + cpf
        """
        if not filename:
            filename = f"{cnh_request.id}.png"
        
        # Gerar nomes das pastas
        user_folder_name = cls.get_user_folder_name(cnh_request.user_id)
        cpf_clean = cls.get_cpf_clean(cnh_request.cpf)
        
        # Construir hierarquia de pastas
        user_folder = os.path.join(cls.BASE_DIR, user_folder_name)
        cpf_folder = os.path.join(user_folder, cpf_clean)
        uploads_folder = os.path.join(cpf_folder, "uploads")
        
        # Criar paths absolutos
        front_path = os.path.join(cpf_folder, "front", filename)
        back_path = os.path.join(cpf_folder, "back", filename)
        qrcode_path = os.path.join(cpf_folder, "qrcode", filename)
        
        # Criar paths relativos para URLs públicas
        front_relative = f"{cls.BASE_DIR}/{user_folder_name}/{cpf_clean}/front/{filename}"
        back_relative = f"{cls.BASE_DIR}/{user_folder_name}/{cpf_clean}/back/{filename}"
        qrcode_relative = f"{cls.BASE_DIR}/{user_folder_name}/{cpf_clean}/qrcode/{filename}"
        
        return CNHPaths(
            user_folder=user_folder,
            cpf_folder=cpf_folder,
            uploads_folder=uploads_folder,
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
        Garante que todos os diretórios necessários existem na nova estrutura.
        
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
        Retorna paths existentes para uma CNH na nova estrutura.
        
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
    def delete_user_cpf_folder(cls, user_id: int, cpf: str) -> bool:
        """
        Remove pasta específica de um CPF de um usuário.
        Nova estrutura: user_{id}/{cpf}/
        
        Args:
            user_id: ID do usuário
            cpf: CPF formatado ou limpo
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            import shutil
            
            user_folder_name = cls.get_user_folder_name(user_id)
            cpf_clean = cls.get_cpf_clean(cpf)
            cpf_folder = os.path.join(cls.BASE_DIR, user_folder_name, cpf_clean)
            
            if os.path.exists(cpf_folder):
                shutil.rmtree(cpf_folder)
                logger.info(f"Pasta do CPF removida: {cpf_folder}")
                return True
            else:
                logger.warning(f"Pasta do CPF não existe: {cpf_folder}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover pasta do CPF {cpf} do usuário {user_id}: {str(e)}")
            return False
    
    @classmethod 
    def delete_user_folder(cls, user_id: int) -> bool:
        """
        Remove toda pasta de um usuário (todas as CNHs do usuário).
        
        Args:
            user_id: ID do usuário
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            import shutil
            
            user_folder_name = cls.get_user_folder_name(user_id)
            user_folder = os.path.join(cls.BASE_DIR, user_folder_name)
            
            if os.path.exists(user_folder):
                shutil.rmtree(user_folder)
                logger.info(f"Pasta do usuário removida: {user_folder}")
                return True
            else:
                logger.warning(f"Pasta do usuário não existe: {user_folder}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover pasta do usuário {user_id}: {str(e)}")
            return False
    
    @classmethod
    def get_legacy_path_mapping(cls, old_path: str, user_id: int) -> Optional[str]:
        """
        Mapeia paths antigos para nova estrutura user_id + cpf.
        
        Args:
            old_path: Path no formato antigo
            user_id: ID do usuário para mapear
            
        Returns:
            str: Path no novo formato ou None
        """
        if not old_path:
            return None
        
        user_folder_name = cls.get_user_folder_name(user_id)
        
        # Mapear estrutura antiga CPF/ -> user_X/CPF/
        if old_path.startswith(f"{cls.BASE_DIR}/") and not old_path.startswith(f"{cls.BASE_DIR}/user_"):
            # Extrair partes do path antigo
            parts = old_path.replace(f"{cls.BASE_DIR}/", "").split('/')
            if len(parts) >= 3:  # cpf/tipo/arquivo
                cpf, tipo, arquivo = parts[0], parts[1], parts[2]
                new_path = f"{cls.BASE_DIR}/{user_folder_name}/{cpf}/{tipo}/{arquivo}"
                return new_path
        
        return None

