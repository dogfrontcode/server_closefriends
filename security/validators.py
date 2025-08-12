# -*- coding: utf-8 -*-
"""
🔍 Security Validators - Validadores de segurança

Implementa validações robustas para dados sensíveis.
"""

import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class SecurityValidator:
    """
    Classe para validações de segurança.
    """
    
    # Padrões maliciosos conhecidos
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS básico
        r'javascript:',                # JavaScript URI
        r'union\s+select',            # SQL injection
        r'drop\s+table',              # SQL injection
        r'insert\s+into',             # SQL injection
        r'delete\s+from',             # SQL injection
        r'update\s+.*\s+set',         # SQL injection
        r'exec\s*\(',                 # Command injection
        r'eval\s*\(',                 # Code injection
        r'../.*/',                    # Path traversal
        r'\.\.\\.*\\',                # Path traversal (Windows)
    ]
    
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
    def validate_cpf(cls, cpf: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida CPF com verificações de segurança.
        
        Args:
            cpf: CPF a ser validado
            
        Returns:
            tuple: (válido: bool, cpf_limpo: str, erro: str)
        """
        if not cpf:
            return False, "", "CPF não fornecido"
        
        # Verificar padrões maliciosos
        cpf_lower = cpf.lower()
        for pattern in cls.MALICIOUS_PATTERNS:
            if re.search(pattern, cpf_lower, re.IGNORECASE):
                logger.warning(f"🚨 Padrão malicioso detectado no CPF: {pattern}")
                return False, "", "CPF contém caracteres inválidos"
        
        # Limpar CPF
        cpf_limpo = re.sub(r'[^\d]', '', cpf)
        
        # Verificar comprimento
        if len(cpf_limpo) != 11:
            return False, cpf_limpo, "CPF deve conter exatamente 11 dígitos"
        
        # Verificar se não são todos dígitos iguais
        if len(set(cpf_limpo)) == 1:
            return False, cpf_limpo, "CPF inválido (todos os dígitos iguais)"
        
        # Validar dígitos verificadores
        if not cls._validate_cpf_digits(cpf_limpo):
            return False, cpf_limpo, "CPF inválido (dígitos verificadores incorretos)"
        
        return True, cpf_limpo, None
    
    @classmethod
    def _validate_cpf_digits(cls, cpf: str) -> bool:
        """
        Valida os dígitos verificadores do CPF.
        
        Args:
            cpf: CPF limpo (apenas números)
            
        Returns:
            bool: CPF válido
        """
        try:
            # Calcular primeiro dígito verificador
            soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
            primeiro_digito = (soma * 10) % 11
            if primeiro_digito == 10:
                primeiro_digito = 0
            
            if int(cpf[9]) != primeiro_digito:
                return False
            
            # Calcular segundo dígito verificador
            soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
            segundo_digito = (soma * 10) % 11
            if segundo_digito == 10:
                segundo_digito = 0
            
            return int(cpf[10]) == segundo_digito
            
        except (ValueError, IndexError):
            return False
    
    @classmethod
    def format_cpf(cls, cpf_limpo: str) -> str:
        """
        Formata CPF limpo no padrão XXX.XXX.XXX-XX.
        
        Args:
            cpf_limpo: CPF apenas com números
            
        Returns:
            str: CPF formatado
        """
        if len(cpf_limpo) != 11:
            return cpf_limpo
        
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    
    @classmethod
    def validate_password(cls, password: str, min_length: int = 4, max_length: int = 20) -> Tuple[bool, str]:
        """
        Valida senha com critérios de segurança.
        
        Args:
            password: Senha a ser validada
            min_length: Comprimento mínimo
            max_length: Comprimento máximo
            
        Returns:
            tuple: (válida: bool, erro: str)
        """
        if not password:
            return False, "Senha não fornecida"
        
        # Verificar padrões maliciosos
        password_lower = password.lower()
        for pattern in cls.MALICIOUS_PATTERNS:
            if re.search(pattern, password_lower, re.IGNORECASE):
                logger.warning("🚨 Padrão malicioso detectado na senha")
                return False, "Senha contém caracteres inválidos"
        
        # Verificar comprimento
        if len(password) < min_length:
            return False, f"Senha deve ter pelo menos {min_length} caracteres"
        
        if len(password) > max_length:
            return False, f"Senha deve ter no máximo {max_length} caracteres"
        
        # Para senhas CNH (4 dígitos), verificar se são apenas números
        if min_length == 4 and max_length == 4:
            if not password.isdigit():
                return False, "Senha deve conter apenas números"
        
        return True, ""
    
    @classmethod
    def sanitize_input(cls, input_str: str, max_length: int = 100) -> str:
        """
        Sanitiza entrada removendo caracteres perigosos.
        
        Args:
            input_str: String a ser sanitizada
            max_length: Comprimento máximo
            
        Returns:
            str: String sanitizada
        """
        if not input_str:
            return ""
        
        # Truncar se muito longo
        sanitized = input_str[:max_length]
        
        # Remover caracteres de controle
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        # Escapar caracteres HTML básicos
        html_escape = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;'
        }
        
        for char, escaped in html_escape.items():
            sanitized = sanitized.replace(char, escaped)
        
        return sanitized.strip()
    
    @classmethod
    def validate_ip_address(cls, ip: str) -> bool:
        """
        Valida endereço IP.
        
        Args:
            ip: Endereço IP
            
        Returns:
            bool: IP válido
        """
        if not ip:
            return False
        
        # Regex para IPv4
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        
        return bool(re.match(ipv4_pattern, ip))
    
    @classmethod
    def is_suspicious_request(cls, data: dict, ip: str) -> Tuple[bool, str]:
        """
        Detecta requisições suspeitas baseado em padrões.
        
        Args:
            data: Dados da requisição
            ip: IP do cliente
            
        Returns:
            tuple: (suspeito: bool, motivo: str)
        """
        reasons = []
        
        # Verificar IP inválido
        if not cls.validate_ip_address(ip):
            reasons.append("IP inválido")
        
        # Verificar dados vazios ou muito grandes
        if not data:
            reasons.append("Dados JSON vazios")
        
        for key, value in data.items():
            if isinstance(value, str):
                # Verificar se o valor é muito longo
                if len(value) > 1000:
                    reasons.append(f"Campo {key} muito longo")
                
                # Verificar padrões maliciosos
                value_lower = value.lower()
                for pattern in cls.MALICIOUS_PATTERNS:
                    if re.search(pattern, value_lower, re.IGNORECASE):
                        reasons.append(f"Padrão malicioso em {key}")
                        break
        
        return len(reasons) > 0, "; ".join(reasons)
