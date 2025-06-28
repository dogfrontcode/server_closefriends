# services/pix_recharge_service.py
import requests
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Configurar logging
logger = logging.getLogger(__name__)

@dataclass
class RechargeConfig:
    """Configuração dos produtos de recarga disponíveis"""
    PRODUCTS = {
        '10.0': {'id': 'HHTVG3Q', 'amount': 10.0},
        '25.0': {'id': '5W8G5ES', 'amount': 25.0},
        '50.0': {'id': 'JYD12K0', 'amount': 50.0},
        '100.0': {'id': 'SDAOB76', 'amount': 100.0}
    }
    
    PHONE_DEFAULT = "(11) 99999-9999"
    DOCUMENT_DEFAULT = "012.345.678-90"  # CPF válido para teste

@dataclass
class FlucsusCredentials:
    """Credenciais da API Flucsus"""
    PUBLIC_KEY = 'galinhada_aktclpxexbzghhx1'
    SECRET_KEY = '4fq962d1pgzdfomyoy7exrifu8kmom73o16yrco5sj4p0zti8gizrj4xk6zivwue'
    API_URL = 'https://app.flucsus.com.br/api/v1/gateway/pix/receive'

@dataclass
class PixRechargeResponse:
    """Resposta da criação de recarga PIX"""
    success: bool
    transaction_id: Optional[str] = None
    pix_code: Optional[str] = None
    qr_code_base64: Optional[str] = None
    order_url: Optional[str] = None
    fee: Optional[float] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict] = None

class PixRechargeService:
    """
    Serviço para gerar recargas PIX via Flucsus
    
    Módulo estruturado e reutilizável para processar pagamentos PIX
    de recarga com valores fixos pré-definidos.
    """
    
    def __init__(self):
        self.credentials = FlucsusCredentials()
        self.config = RechargeConfig()
    
    def get_available_amounts(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna os valores de recarga disponíveis
        
        Returns:
            Dict: Dicionário com valores e IDs dos produtos
        """
        return self.config.PRODUCTS.copy()
    
    def validate_amount(self, amount: float) -> bool:
        """
        Valida se o valor é permitido
        
        Args:
            amount (float): Valor a ser validado
            
        Returns:
            bool: True se o valor é válido, False caso contrário
        """
        return str(amount) in self.config.PRODUCTS
    
    def generate_identifier(self) -> str:
        """
        Gera identificador único para a transação
        
        Returns:
            str: Identificador único
        """
        return str(uuid.uuid4()).replace('-', '')[:10]
    
    def build_payload(self, username: str, amount: float, identifier: str = None) -> Dict[str, Any]:
        """
        Constrói o payload para a API Flucsus
        
        Args:
            username (str): Nome do usuário
            amount (float): Valor da recarga
            identifier (str, optional): Identificador da transação
            
        Returns:
            Dict: Payload para envio à API
            
        Raises:
            ValueError: Se o valor não for válido
        """
        if not self.validate_amount(amount):
            raise ValueError(f"Valor {amount} não é permitido. Valores válidos: {list(self.config.PRODUCTS.keys())}")
        
        if not identifier:
            identifier = self.generate_identifier()
        
        product_info = self.config.PRODUCTS[str(amount)]
        
        # Data de vencimento (1 dia)
        due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        payload = {
            "identifier": identifier,
            "amount": amount,
            "client": {
                "name": username,
                "email": f"{username.lower()}@base.com",
                "phone": self.config.PHONE_DEFAULT,
                "document": self.config.DOCUMENT_DEFAULT
            },
            "products": [
                {
                    "id": product_info['id'],
                    "name": "RECARGA",
                    "quantity": 1,
                    "price": amount
                }
            ],
            "dueDate": due_date
        }
        
        return payload
    
    def get_headers(self) -> Dict[str, str]:
        """
        Retorna headers para a requisição à API Flucsus
        
        Returns:
            Dict: Headers da requisição
        """
        return {
            'Content-Type': 'application/json',
            'x-public-key': self.credentials.PUBLIC_KEY,
            'x-secret-key': self.credentials.SECRET_KEY
        }
    
    def create_recharge(self, username: str, amount: float, identifier: str = None, timeout: int = 30) -> PixRechargeResponse:
        """
        Cria uma recarga PIX via API Flucsus
        
        Args:
            username (str): Nome do usuário
            amount (float): Valor da recarga
            identifier (str, optional): Identificador da transação
            timeout (int): Timeout da requisição em segundos
            
        Returns:
            PixRechargeResponse: Resposta da criação da recarga
        """
        try:
            # Validar entrada
            if not username or not username.strip():
                return PixRechargeResponse(
                    success=False,
                    error_message="Nome do usuário é obrigatório"
                )
            
            # Gerar identificador se não fornecido
            if not identifier:
                identifier = self.generate_identifier()
            
            # Construir payload
            payload = self.build_payload(username, amount, identifier)
            headers = self.get_headers()
            
            logger.info(f"Criando recarga PIX - Usuário: {username}, Valor: R$ {amount:.2f}, ID: {identifier}")
            
            # Fazer requisição
            response = requests.post(
                self.credentials.API_URL,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            logger.info(f"Flucsus response status: {response.status_code}")
            
            # Processar resposta
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Flucsus response data: {data}")
                
                if data.get('status') == 'OK':
                    pix_data = data.get('pix', {})
                    order_data = data.get('order', {})
                    
                    return PixRechargeResponse(
                        success=True,
                        transaction_id=data.get('transactionId'),
                        pix_code=pix_data.get('code'),
                        qr_code_base64=pix_data.get('base64'),
                        order_url=order_data.get('url'),
                        fee=data.get('fee'),
                        raw_response=data
                    )
                else:
                    return PixRechargeResponse(
                        success=False,
                        error_message=f"API retornou status: {data.get('status')}",
                        raw_response=data
                    )
            
            elif response.status_code == 422:
                # Erro de validação
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Erro de validação')
                except:
                    error_msg = 'Erro de validação - dados inválidos'
                
                logger.error(f"Erro de validação Flucsus: {error_msg}")
                return PixRechargeResponse(
                    success=False,
                    error_message=error_msg,
                    raw_response=error_data if 'error_data' in locals() else None
                )
            
            else:
                # Outros erros HTTP
                error_msg = f"Erro HTTP {response.status_code}: {response.text}"
                logger.error(f"Erro Flucsus: {error_msg}")
                return PixRechargeResponse(
                    success=False,
                    error_message=error_msg
                )
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout na conexão com a API Flucsus"
            logger.error(error_msg)
            return PixRechargeResponse(
                success=False,
                error_message=error_msg
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão: {str(e)}"
            logger.error(error_msg)
            return PixRechargeResponse(
                success=False,
                error_message=error_msg
            )
            
        except ValueError as e:
            # Erro de validação de valor
            logger.error(f"Erro de validação: {str(e)}")
            return PixRechargeResponse(
                success=False,
                error_message=str(e)
            )
            
        except Exception as e:
            error_msg = f"Erro interno: {str(e)}"
            logger.error(error_msg)
            return PixRechargeResponse(
                success=False,
                error_message=error_msg
            )
    
    def get_product_info(self, amount: float) -> Optional[Dict[str, Any]]:
        """
        Obtém informações do produto pela quantidade
        
        Args:
            amount (float): Valor da recarga
            
        Returns:
            Dict: Informações do produto ou None se não encontrado
        """
        return self.config.PRODUCTS.get(str(amount))

# Instância singleton do serviço
pix_recharge_service = PixRechargeService() 