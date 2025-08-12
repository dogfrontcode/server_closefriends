# -*- coding: utf-8 -*-
"""
🛡️ Rate Limiter - Sistema de proteção contra força bruta

Implementa rate limiting por IP e CPF para prevenir ataques.
"""

import time
import logging
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Sistema de rate limiting com múltiplas estratégias.
    """
    
    def __init__(self):
        # Armazena tentativas por IP
        self.ip_attempts = defaultdict(deque)
        # Armazena tentativas por CPF
        self.cpf_attempts = defaultdict(deque)
        # Armazena IPs bloqueados temporariamente
        self.blocked_ips = {}
        # Armazena CPFs bloqueados temporariamente
        self.blocked_cpfs = {}
    
    def _cleanup_old_attempts(self, attempts_deque, window_seconds=300):
        """Remove tentativas antigas da janela de tempo."""
        current_time = time.time()
        while attempts_deque and attempts_deque[0] < current_time - window_seconds:
            attempts_deque.popleft()
    
    def _is_blocked(self, identifier, blocked_dict):
        """Verifica se um identificador está bloqueado."""
        if identifier in blocked_dict:
            if time.time() < blocked_dict[identifier]:
                return True
            else:
                # Remover bloqueio expirado
                del blocked_dict[identifier]
        return False
    
    def check_rate_limit(self, ip_address, cpf=None, max_attempts=5, window_seconds=300, block_seconds=900):
        """
        Verifica se uma requisição deve ser permitida.
        
        Args:
            ip_address: IP do cliente
            cpf: CPF sendo consultado (opcional)
            max_attempts: Máximo de tentativas na janela
            window_seconds: Janela de tempo em segundos (default: 5 min)
            block_seconds: Tempo de bloqueio em segundos (default: 15 min)
            
        Returns:
            tuple: (permitido: bool, motivo: str, retry_after: int)
        """
        current_time = time.time()
        
        # Verificar se IP está bloqueado
        if self._is_blocked(ip_address, self.blocked_ips):
            retry_after = int(self.blocked_ips[ip_address] - current_time)
            return False, f"IP bloqueado por força bruta. Tente novamente em {retry_after}s", retry_after
        
        # Verificar se CPF está bloqueado
        if cpf and self._is_blocked(cpf, self.blocked_cpfs):
            retry_after = int(self.blocked_cpfs[cpf] - current_time)
            return False, f"CPF bloqueado por força bruta. Tente novamente em {retry_after}s", retry_after
        
        # Limpar tentativas antigas do IP
        self._cleanup_old_attempts(self.ip_attempts[ip_address], window_seconds)
        
        # Verificar limite por IP
        if len(self.ip_attempts[ip_address]) >= max_attempts:
            # Bloquear IP
            self.blocked_ips[ip_address] = current_time + block_seconds
            logger.warning(f"🚨 IP bloqueado por força bruta: {ip_address}")
            return False, f"Muitas tentativas do IP. Bloqueado por {block_seconds//60} minutos", block_seconds
        
        # Se há CPF, verificar limite por CPF
        if cpf:
            self._cleanup_old_attempts(self.cpf_attempts[cpf], window_seconds)
            
            if len(self.cpf_attempts[cpf]) >= max_attempts:
                # Bloquear CPF
                self.blocked_cpfs[cpf] = current_time + block_seconds
                logger.warning(f"🚨 CPF bloqueado por força bruta: {cpf[:3]}***")
                return False, f"Muitas tentativas para este CPF. Bloqueado por {block_seconds//60} minutos", block_seconds
        
        return True, "OK", 0
    
    def record_attempt(self, ip_address, cpf=None, success=False):
        """
        Registra uma tentativa de login.
        
        Args:
            ip_address: IP do cliente
            cpf: CPF consultado
            success: Se a tentativa foi bem-sucedida
        """
        current_time = time.time()
        
        if not success:
            # Só registrar tentativas falhadas
            self.ip_attempts[ip_address].append(current_time)
            
            if cpf:
                self.cpf_attempts[cpf].append(current_time)
            
            logger.info(f"🔍 Tentativa de login falhada registrada - IP: {ip_address}, CPF: {cpf[:3] + '***' if cpf else 'N/A'}")
        else:
            # Limpar tentativas em caso de sucesso
            if ip_address in self.ip_attempts:
                self.ip_attempts[ip_address].clear()
            
            if cpf and cpf in self.cpf_attempts:
                self.cpf_attempts[cpf].clear()
            
            logger.info(f"✅ Login bem-sucedido - tentativas limpas para IP: {ip_address}")
    
    def get_stats(self):
        """Retorna estatísticas do rate limiter."""
        return {
            "ips_tracking": len(self.ip_attempts),
            "cpfs_tracking": len(self.cpf_attempts),
            "ips_blocked": len(self.blocked_ips),
            "cpfs_blocked": len(self.blocked_cpfs)
        }

# Instância global do rate limiter
rate_limiter = RateLimiter()

def rate_limit_decorator(max_attempts=5, window_seconds=300, block_seconds=900):
    """
    Decorator para aplicar rate limiting em endpoints.
    
    Args:
        max_attempts: Máximo de tentativas na janela
        window_seconds: Janela de tempo em segundos
        block_seconds: Tempo de bloqueio em segundos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obter IP do cliente
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            # Tentar obter CPF do request
            cpf = None
            if request.is_json:
                data = request.get_json()
                if data and 'cpf' in data:
                    cpf = ''.join(filter(str.isdigit, data['cpf']))
            
            # Verificar rate limit
            allowed, reason, retry_after = rate_limiter.check_rate_limit(
                ip_address, cpf, max_attempts, window_seconds, block_seconds
            )
            
            if not allowed:
                response = jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'message': reason,
                    'retry_after': retry_after
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                return response
            
            # Executar função original
            result = f(*args, **kwargs)
            
            # Registrar tentativa baseada no status da resposta
            if hasattr(result, 'status_code'):
                success = result.status_code == 200
                rate_limiter.record_attempt(ip_address, cpf, success)
            
            return result
        
        return decorated_function
    return decorator
