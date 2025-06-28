# controllers/pix_payment.py
from flask import Blueprint, request, jsonify, session
from models.user import User
from models.credit_transaction import CreditTransaction
from models import db
import logging
from datetime import datetime

# Importar o novo serviço modular
from services.pix_recharge_service import pix_recharge_service

# Configurar logging
logger = logging.getLogger(__name__)

# Blueprint para rotas de pagamento PIX
pix_bp = Blueprint('pix', __name__, url_prefix='/api/pix')

# ==================== MIDDLEWARE DE AUTENTICAÇÃO ====================

def require_auth():
    """Verifica se o usuário está autenticado"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    return None

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
        
        # Salvar transação pendente no banco
        pending_transaction = CreditTransaction(
            user_id=user.id,
            amount=amount,
            transaction_type='pix_pending',
            description=f'PIX R$ {amount:.2f} - Aguardando pagamento',
            reference_id=response.transaction_id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(pending_transaction)
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
    Verifica o status de um pagamento PIX
    
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
        
        # Buscar transação pendente
        pending_transaction = CreditTransaction.query.filter_by(
            user_id=user.id,
            reference_id=payment_id
        ).first()
        
        if not pending_transaction:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        
        # Determinar status baseado no tipo de transação
        is_paid = pending_transaction.transaction_type == 'pix_confirmed'
        status = 'COMPLETED' if is_paid else 'PENDING'
        
        return jsonify({
            'success': True,
            'status': status,
            'payment_id': payment_id,
            'isPaid': is_paid,
            'amount': pending_transaction.amount,
            'transaction_type': pending_transaction.transaction_type
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
            user.add_credits(
                amount=amount,
                transaction_type='pix_confirmed',
                description=f'PIX R$ {amount:.2f} - Pagamento confirmado'
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
    Webhook para receber notificações do gateway de pagamento Flucsus
    """
    try:
        data = request.get_json()
        logger.info(f"Webhook Flucsus recebido: {data}")
        
        # Aqui você processará os dados do webhook da Flucsus
        # e chamará confirm_payment() internamente
        
        # Exemplo de processamento:
        # transaction_id = data.get('transactionId')
        # status = data.get('status')
        # 
        # if transaction_id and status:
        #     confirm_payment_internal(transaction_id, status)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500 