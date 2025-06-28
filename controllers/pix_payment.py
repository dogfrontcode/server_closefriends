# controllers/pix_payment.py
from flask import Blueprint, request, jsonify, session
from models.user import User
from models.credit_transaction import CreditTransaction
from models import db
import logging
import requests
from datetime import datetime

# Importar o novo serviço modular
from services.pix_recharge_service import pix_recharge_service

# Configurar logging
logger = logging.getLogger(__name__)

# Blueprint para rotas de pagamento PIX
pix_bp = Blueprint('pix', __name__, url_prefix='/api/pix')

# Configurações da Flucsus
FLUCSUS_CONFIG = {
    'public_key': 'galinhada_aktclpxexbzghhx1',
    'secret_key': '4fq962d1pgzdfomyoy7exrifu8kmom73o16yrco5sj4p0zti8gizrj4xk6zivwue',
    'api_url': 'https://app.flucsus.com.br/api/v1'
}

# ==================== MIDDLEWARE DE AUTENTICAÇÃO ====================

def require_auth():
    """Verifica se o usuário está autenticado"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    return None

# ==================== FUNÇÃO DE CONSULTA FLUCSUS ====================

def check_payment_status_flucsus(transaction_id):
    """
    Verifica o status de um pagamento diretamente na API da Flucsus
    
    Args:
        transaction_id (str): ID da transação na Flucsus
        
    Returns:
        dict: Dados do status do pagamento
    """
    try:
        logger.info(f"🔍 Verificando status do pagamento na Flucsus: {transaction_id}")
        
        # Consultar diretamente a API da Flucsus
        flucsus_response = requests.get(
            f"{FLUCSUS_CONFIG['api_url']}/gateway/transactions?id={transaction_id}",
            headers={
                'x-public-key': FLUCSUS_CONFIG['public_key'],
                'x-secret-key': FLUCSUS_CONFIG['secret_key'],
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if flucsus_response.status_code == 200:
            flucsus_data = flucsus_response.json()
            logger.info(f"📊 Status da Flucsus: {flucsus_data.get('status', 'UNKNOWN')}")
            
            # Verificar se foi pago
            is_completed = flucsus_data.get('status') == 'COMPLETED'
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': flucsus_data.get('status', 'PENDING'),
                'is_paid': is_completed,
                'is_completed': is_completed,
                'flucsus_status': flucsus_data.get('status'),
                'payed_at': flucsus_data.get('payedAt'),
                'amount': flucsus_data.get('amount'),
                'source': 'flucsus_api',
                'message': 'Pagamento confirmado na Flucsus' if is_completed else 'Pagamento ainda pendente',
                'raw_data': flucsus_data
            }
        else:
            logger.error(f"❌ Erro na consulta Flucsus: {flucsus_response.status_code}")
            return {
                'success': False,
                'error': f'Erro na consulta Flucsus: {flucsus_response.status_code}',
                'source': 'flucsus_api'
            }
            
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout ao consultar Flucsus")
        return {
            'success': False,
            'error': 'Timeout ao consultar Flucsus',
            'source': 'flucsus_api'
        }
    except Exception as e:
        logger.error(f"❌ Erro ao consultar Flucsus: {str(e)}")
        return {
            'success': False,
            'error': f'Erro ao consultar Flucsus: {str(e)}',
            'source': 'flucsus_api'
        }

# ==================== ENDPOINTS DE PAGAMENTO PIX ====================

@pix_bp.route('/create-payment', methods=['POST'])
def create_pix_payment():
    """
    Cria um pagamento PIX para recarga de créditos usando serviço modular
    
    Body:
        amount (float): Valor em reais a ser carregado
        
    Returns:
        JSON: Dados do PIX (QR code, código, etc.)
    """
    try:
        # Verificar autenticação
        auth_error = require_auth()
        if auth_error:
            return auth_error
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        if not data or 'amount' not in data:
            return jsonify({'error': 'Valor do pagamento é obrigatório'}), 400
        
        amount = float(data['amount'])
        
        # Validar valor usando o serviço
        if not pix_recharge_service.validate_amount(amount):
            available_amounts = list(pix_recharge_service.get_available_amounts().keys())
            return jsonify({
                'error': f'Valores permitidos: R$ {", ".join(available_amounts)}'
            }), 400
        
        # Criar recarga usando o serviço modular
        response = pix_recharge_service.create_recharge(
            username=user.username,
            amount=amount
        )
        
        if not response.success:
            logger.error(f"Erro ao criar recarga PIX: {response.error_message}")
            return jsonify({'error': response.error_message}), 500
        
        # Salvar transação pendente no banco usando método correto
        pending_transaction = CreditTransaction.create_transaction(
            user_id=user.id,
            amount=amount,  # Manter valor real para referência
            transaction_type='pix_pending',
            description=f'PIX R$ {amount:.2f} - Aguardando pagamento',
            balance_before=user.credits,
            balance_after=user.credits,  # Saldo não muda para pendente
            reference_id=response.transaction_id
        )
        
        db.session.commit()
        
        # Mapear resposta para o frontend
        response_data = {
            'success': True,
            'status': 'OK',
            'payment_id': response.transaction_id,
            'transaction_id': pending_transaction.id,
            'amount': amount,
            'pix': {
                'code': response.pix_code,
                'base64': response.qr_code_base64,
                'qr_code_url': f'data:image/png;base64,{response.qr_code_base64}' if response.qr_code_base64 else ''
            },
            'order_url': response.order_url,
            'fee': response.fee,
            'expires_at': (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat()
        }
        
        logger.info(f"Recarga PIX criada com sucesso - User: {user.username}, Valor: R$ {amount:.2f}, ID: {response.transaction_id}")
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        logger.error(f"Erro de valor: {str(e)}")
        return jsonify({'error': 'Valor inválido'}), 400
    except Exception as e:
        logger.error(f"Erro interno ao criar pagamento PIX: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@pix_bp.route('/available-amounts', methods=['GET'])
def get_available_amounts():
    """
    Retorna os valores de recarga disponíveis
    
    Returns:
        JSON: Lista dos valores disponíveis com seus IDs
    """
    try:
        # Verificar autenticação
        auth_error = require_auth()
        if auth_error:
            return auth_error
        
        amounts = pix_recharge_service.get_available_amounts()
        
        # Formatar resposta para o frontend
        formatted_amounts = []
        for amount_str, product_info in amounts.items():
            formatted_amounts.append({
                'amount': product_info['amount'],
                'id': product_info['id'],
                'formatted': f"R$ {product_info['amount']:.2f}"
            })
        
        return jsonify({
            'success': True,
            'amounts': formatted_amounts
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter valores disponíveis: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@pix_bp.route('/check-payment/<payment_id>', methods=['GET'])
def check_payment_status(payment_id):
    """
    Verifica o status de um pagamento PIX consultando DIRETAMENTE a Flucsus
    
    Args:
        payment_id (str): ID do pagamento
        
    Returns:
        JSON: Status do pagamento
    """
    try:
        # Verificar autenticação
        auth_error = require_auth()
        if auth_error:
            return auth_error
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Buscar transação pendente no banco local
        pending_transaction = CreditTransaction.query.filter_by(
            user_id=user.id,
            reference_id=payment_id
        ).first()
        
        if not pending_transaction:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        
        # 🚀 CONSULTAR DIRETAMENTE A FLUCSUS PRIMEIRO
        flucsus_result = check_payment_status_flucsus(payment_id)
        
        if flucsus_result['success']:
            # Se conseguiu consultar a Flucsus
            if flucsus_result['is_completed'] and pending_transaction.transaction_type == 'pix_pending':
                # Pagamento foi confirmado na Flucsus, vamos processar localmente
                logger.info(f"✅ Pagamento confirmado na Flucsus, processando: {payment_id}")
                
                # Adicionar créditos ao usuário
                amount = pending_transaction.amount
                old_balance = user.credits
                user.credits += amount
                
                # Criar nova transação de confirmação
                confirmed_transaction = CreditTransaction.create_transaction(
                    user_id=user.id,
                    amount=amount,
                    transaction_type='pix_confirmed',
                    description=f'PIX R$ {amount:.2f} - Pagamento confirmado',
                    balance_before=old_balance,
                    balance_after=user.credits,
                    reference_id=payment_id
                )
                
                # Atualizar transação pendente para confirmada
                pending_transaction.transaction_type = 'pix_confirmed'
                pending_transaction.description = f'PIX R$ {amount:.2f} - Pagamento confirmado'
                
                db.session.commit()
                
                logger.info(f'💰 Créditos adicionados - User: {user.username}, Valor: R$ {amount:.2f}, Novo saldo: R$ {user.credits:.2f}')
            
            # ✅ PRIORIZAR STATUS LOCAL SE JÁ FOI CONFIRMADO
            is_locally_confirmed = pending_transaction.transaction_type == 'pix_confirmed'
            final_is_paid = flucsus_result['is_completed'] or is_locally_confirmed
            final_status = 'COMPLETED' if final_is_paid else 'PENDING'
            
            # Determinar a fonte mais confiável
            source = 'flucsus_api' if flucsus_result['is_completed'] else ('local_confirmed' if is_locally_confirmed else 'flucsus_api')
            message = flucsus_result.get('message')
            if is_locally_confirmed and not flucsus_result['is_completed']:
                message = 'Pagamento confirmado localmente via webhook'
            
            return jsonify({
                'success': True,
                'status': final_status,
                'payment_id': payment_id,
                'isPaid': final_is_paid,
                'amount': pending_transaction.amount,
                'transaction_type': pending_transaction.transaction_type,
                'source': source,
                'flucsus_status': flucsus_result.get('flucsus_status'),
                'payed_at': flucsus_result.get('payed_at'),
                'message': message
            }), 200
        else:
            # ⚠️ FALLBACK: Se Flucsus falhar, usar status local
            logger.warning(f"❌ Falha ao consultar Flucsus, usando fallback local: {flucsus_result.get('error')}")
            
            is_paid = pending_transaction.transaction_type == 'pix_confirmed'
            status = 'COMPLETED' if is_paid else 'PENDING'
            
            return jsonify({
                'success': True,
                'status': status,
                'payment_id': payment_id,
                'isPaid': is_paid,
                'amount': pending_transaction.amount,
                'transaction_type': pending_transaction.transaction_type,
                'source': 'local_fallback',
                'flucsus_error': flucsus_result.get('error'),
                'message': 'Status obtido do banco local (Flucsus indisponível)'
            }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar status do pagamento: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@pix_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    """
    Confirma um pagamento PIX (para ser chamado via webhook)
    
    Body:
        payment_id (str): ID do pagamento
        status (str): Status do pagamento
        
    Returns:
        JSON: Confirmação
    """
    try:
        data = request.get_json()
        if not data or 'payment_id' not in data:
            return jsonify({'error': 'ID do pagamento é obrigatório'}), 400
        
        payment_id = data['payment_id']
        status = data.get('status', 'COMPLETED')
        
        # Buscar transação pendente
        pending_transaction = CreditTransaction.query.filter_by(
            reference_id=payment_id,
            transaction_type='pix_pending'
        ).first()
        
        if not pending_transaction:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        
        if status == 'COMPLETED':
            # Buscar usuário
            user = User.query.get(pending_transaction.user_id)
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            
            # Adicionar créditos
            amount = pending_transaction.amount
            old_balance = user.credits
            user.credits += amount
            
            # Criar nova transação de confirmação
            confirmed_transaction = CreditTransaction.create_transaction(
                user_id=user.id,
                amount=amount,
                transaction_type='pix_confirmed',
                description=f'PIX R$ {amount:.2f} - Pagamento confirmado',
                balance_before=old_balance,
                balance_after=user.credits,
                reference_id=payment_id
            )
            
            # Atualizar transação pendente
            pending_transaction.transaction_type = 'pix_confirmed'
            pending_transaction.description = f'PIX R$ {amount:.2f} - Pagamento confirmado'
            
            db.session.commit()
            
            logger.info(f"Pagamento PIX confirmado - User: {user.username}, Valor: R$ {amount:.2f}, ID: {payment_id}")
            
            return jsonify({
                'success': True,
                'message': 'Pagamento confirmado com sucesso',
                'amount': amount,
                'new_balance': user.credits
            }), 200
        else:
            # Pagamento falhou ou foi cancelado
            amount = pending_transaction.amount
            pending_transaction.transaction_type = 'pix_failed'
            pending_transaction.description = f'PIX R$ {amount:.2f} - Pagamento falhou'
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': 'Pagamento não foi aprovado'
            }), 200
            
    except Exception as e:
        logger.error(f"Erro ao confirmar pagamento: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== ENDPOINTS DE WEBHOOK ====================

@pix_bp.route('/webhook', methods=['POST'])
def webhook_payment():
    """
    🔔 Webhook para receber notificações do gateway de pagamento Flucsus
    
    Baseado no padrão fornecido em Node.js
    """
    try:
        # Obter dados do webhook
        data = request.get_json()
        headers = dict(request.headers)
        
        logger.info('🔔 Webhook de pagamento recebido')
        logger.info(f'📋 Headers: {headers}')
        logger.info(f'📦 Body: {data}')
        
        # Log detalhado do payload
        logger.info(f'💳 Payload do webhook: {data}')
        
        # Verificar se é o evento TRANSACTION_PAID
        if data and data.get('event') == 'TRANSACTION_PAID':
            logger.info('✅ Pagamento confirmado recebido!')
            
            transaction_data = data.get('transaction', {})
            client_data = data.get('client', {})
            order_items = data.get('orderItems', [])
            
            transaction_id = transaction_data.get('id')
            client_id = client_data.get('id')
            
            if transaction_id:
                logger.info(f'💰 Processando pagamento {transaction_id}')
                logger.info(f'👤 Cliente: {client_data.get("name")} ({client_data.get("email")})')
                
                if order_items:
                    product_names = [item.get('product', {}).get('name', 'N/A') for item in order_items]
                    logger.info(f'🛍️ Produtos: {", ".join(product_names)}')
                
                # Buscar transação pendente no banco
                pending_transaction = CreditTransaction.query.filter_by(
                    reference_id=transaction_id,
                    transaction_type='pix_pending'
                ).first()
                
                if pending_transaction:
                    # Buscar usuário
                    user = User.query.get(pending_transaction.user_id)
                    if user:
                        # Adicionar créditos
                        amount = pending_transaction.amount
                        old_balance = user.credits
                        user.credits += amount
                        
                        # Criar nova transação de confirmação
                        confirmed_transaction = CreditTransaction.create_transaction(
                            user_id=user.id,
                            amount=amount,
                            transaction_type='pix_confirmed',
                            description=f'PIX R$ {amount:.2f} - Pagamento confirmado (webhook)',
                            balance_before=old_balance,
                            balance_after=user.credits,
                            reference_id=transaction_id
                        )
                        
                        # Atualizar transação pendente
                        pending_transaction.transaction_type = 'pix_confirmed'
                        pending_transaction.description = f'PIX R$ {amount:.2f} - Pagamento confirmado (webhook)'
                        
                        db.session.commit()
                        
                        logger.info(f'💰 Pagamento {transaction_id} processado com sucesso')
                        logger.info(f'💳 Créditos adicionados: R$ {amount:.2f}')
                        logger.info(f'📊 Novo saldo: R$ {user.credits:.2f}')
                    else:
                        logger.error(f'❌ Usuário não encontrado para transação {transaction_id}')
                else:
                    logger.warning(f'⚠️ Transação pendente não encontrada: {transaction_id}')
            else:
                logger.warning('⚠️ Transaction ID não encontrado no webhook')
        else:
            event_type = data.get('event', 'UNKNOWN') if data else 'NO_DATA'
            logger.info(f'📝 Evento ignorado: {event_type}')
        
        # Responder com sucesso (importante para o gateway não reenviar)
        return jsonify({
            'success': True,
            'message': 'Webhook processado com sucesso',
            'received': True
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Erro no webhook de pagamento: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao processar webhook',
            'message': str(e)
        }), 400 