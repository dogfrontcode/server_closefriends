# controllers/credits.py
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.credit_transaction import CreditTransaction
from models import db
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Blueprint para rotas de créditos
credits_bp = Blueprint('credits', __name__, url_prefix='/api/credits')

# ==================== MIDDLEWARE DE AUTENTICAÇÃO ====================

def get_current_user():
    """
    Obtém o usuário atual da sessão ou JWT.
    
    Returns:
        User: Usuário autenticado ou None
    """
    # Tenta via sessão primeiro
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    
    # Se não, tenta via JWT
    try:
        user_id = get_jwt_identity()
        if user_id:
            return User.query.get(user_id)
    except:
        pass
    
    return None

def require_auth():
    """
    Decorator para verificar autenticação.
    
    Returns:
        tuple: (error_response, status_code) se não autenticado, senão (None, None)
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuário não autenticado"}), 401
    return None, None

# ==================== ENDPOINTS DE SALDO ====================

@credits_bp.route('/balance', methods=['GET'])
def get_balance():
    """
    Obtém o saldo atual de créditos do usuário.
    
    Returns:
        JSON: Informações do saldo atual
    """
    try:
        # Verificar autenticação
        error_response, status_code = require_auth()
        if error_response:
            return error_response, status_code
        
        user = get_current_user()
        balance_info = user.get_credit_balance()
        
        # Adicionar estatísticas extras
        total_added = CreditTransaction.get_total_credits_added(user.id)
        total_spent = CreditTransaction.get_total_credits_spent(user.id)
        
        response_data = {
            **balance_info,
            'statistics': {
                'total_added': total_added,
                'total_spent': total_spent,
                'total_transactions': len(user.credit_transactions)
            }
        }
        
        logger.info(f"Saldo consultado - User: {user.username}, Saldo: {balance_info['balance']}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Erro ao consultar saldo - Erro: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@credits_bp.route('/add', methods=['POST'])
def add_credits():
    """
    Adiciona créditos ao usuário (apenas admin ou sistema).
    
    Body:
        amount (float): Valor a adicionar
        transaction_type (str): Tipo da transação
        description (str, optional): Descrição
        
    Returns:
        JSON: Informações da transação criada
    """
    try:
        # Verificar autenticação
        error_response, status_code = require_auth()
        if error_response:
            return error_response, status_code
        
        user = get_current_user()
        data = request.get_json()
        
        # Validar dados
        if not data or 'amount' not in data or 'transaction_type' not in data:
            return jsonify({"error": "Dados obrigatórios: amount, transaction_type"}), 400
        
        amount = float(data['amount'])
        transaction_type = data['transaction_type']
        description = data.get('description')
        
        # Capturar metadados da requisição
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')[:255]
        
        # Adicionar créditos
        transaction = user.add_credits(
            amount=amount,
            transaction_type=transaction_type,
            description=description
        )
        
        # Adicionar metadados à transação
        transaction.ip_address = ip_address
        transaction.user_agent = user_agent
        db.session.commit()
        
        logger.info(f"Créditos adicionados via API - User: {user.username}, Valor: {amount}")
        
        return jsonify({
            "message": "Créditos adicionados com sucesso",
            "transaction": transaction.get_transaction_info(),
            "new_balance": user.get_credit_balance()
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao adicionar créditos - User: {user.username if 'user' in locals() else 'N/A'}, Erro: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500

# ==================== ENDPOINTS DE HISTÓRICO ====================

@credits_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """
    Obtém o histórico de transações do usuário.
    
    Query Params:
        limit (int): Limite de resultados (padrão: 20, máximo: 100)
        offset (int): Offset para paginação (padrão: 0)
        type (str): Filtrar por tipo de transação
        
    Returns:
        JSON: Lista de transações
    """
    try:
        # Verificar autenticação
        error_response, status_code = require_auth()
        if error_response:
            return error_response, status_code
        
        user = get_current_user()
        
        # Parâmetros de query
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        transaction_type = request.args.get('type')
        
        # Buscar transações
        transactions = CreditTransaction.get_user_transactions(
            user_id=user.id,
            limit=limit,
            offset=offset,
            transaction_type=transaction_type
        )
        
        # Formatar dados
        transactions_data = [t.get_transaction_info() for t in transactions]
        
        # Contar total para paginação
        total_query = CreditTransaction.query.filter_by(user_id=user.id)
        if transaction_type:
            total_query = total_query.filter_by(transaction_type=transaction_type)
        total_count = total_query.count()
        
        response_data = {
            'transactions': transactions_data,
            'metadata': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            }
        }
        
        logger.info(f"Histórico consultado - User: {user.username}, Count: {len(transactions_data)}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Erro ao consultar histórico - Erro: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@credits_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
def get_transaction_detail(transaction_id):
    """
    Obtém detalhes de uma transação específica.
    
    Args:
        transaction_id (int): ID da transação
        
    Returns:
        JSON: Detalhes da transação
    """
    try:
        # Verificar autenticação
        error_response, status_code = require_auth()
        if error_response:
            return error_response, status_code
        
        user = get_current_user()
        
        # Buscar transação
        transaction = CreditTransaction.query.filter_by(
            id=transaction_id,
            user_id=user.id
        ).first()
        
        if not transaction:
            return jsonify({"error": "Transação não encontrada"}), 404
        
        return jsonify({
            "transaction": transaction.get_transaction_info()
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao consultar transação - ID: {transaction_id}, Erro: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500

# ==================== ENDPOINTS DE ESTATÍSTICAS ====================

@credits_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Obtém estatísticas de créditos do usuário.
    
    Query Params:
        days (int): Últimos X dias (padrão: 30)
        
    Returns:
        JSON: Estatísticas detalhadas
    """
    try:
        # Verificar autenticação
        error_response, status_code = require_auth()
        if error_response:
            return error_response, status_code
        
        user = get_current_user()
        days = int(request.args.get('days', 30))
        
        # Calcular estatísticas
        total_added = CreditTransaction.get_total_credits_added(user.id, days)
        total_spent = CreditTransaction.get_total_credits_spent(user.id, days)
        total_added_all_time = CreditTransaction.get_total_credits_added(user.id)
        total_spent_all_time = CreditTransaction.get_total_credits_spent(user.id)
        
        # Transações por tipo
        from sqlalchemy import func
        type_stats = db.session.query(
            CreditTransaction.transaction_type,
            func.count(CreditTransaction.id).label('count'),
            func.sum(CreditTransaction.amount).label('total')
        ).filter_by(user_id=user.id).group_by(CreditTransaction.transaction_type).all()
        
        type_breakdown = {}
        for stat in type_stats:
            type_breakdown[stat.transaction_type] = {
                'count': stat.count,
                'total': float(stat.total) if stat.total else 0.0,
                'description': CreditTransaction.TRANSACTION_TYPES.get(stat.transaction_type, stat.transaction_type)
            }
        
        response_data = {
            'current_balance': user.get_credit_balance(),
            'period_stats': {
                'days': days,
                'credits_added': total_added,
                'credits_spent': total_spent,
                'net_change': total_added - total_spent
            },
            'all_time_stats': {
                'credits_added': total_added_all_time,
                'credits_spent': total_spent_all_time,
                'net_total': total_added_all_time - total_spent_all_time
            },
            'transaction_types': type_breakdown
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Erro ao consultar estatísticas - Erro: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500

# ==================== ENDPOINTS DE VERIFICAÇÃO ====================

@credits_bp.route('/check/<float:amount>', methods=['GET'])
def check_sufficient_credits(amount):
    """
    Verifica se o usuário tem créditos suficientes.
    
    Args:
        amount (float): Valor a verificar
        
    Returns:
        JSON: Status da verificação
    """
    try:
        # Verificar autenticação
        error_response, status_code = require_auth()
        if error_response:
            return error_response, status_code
        
        user = get_current_user()
        has_sufficient = user.has_sufficient_credits(amount)
        
        return jsonify({
            "has_sufficient_credits": has_sufficient,
            "required_amount": amount,
            "current_balance": user.credits,
            "shortage": max(0, amount - user.credits) if not has_sufficient else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar créditos - Valor: {amount}, Erro: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500 