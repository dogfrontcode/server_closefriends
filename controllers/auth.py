# controllers/auth.py
from flask import request, jsonify, redirect, url_for, session, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from models import db
from . import auth_bp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registra um novo usuário.

    Requer um payload JSON com os parâmetros:
      - username: nome de usuário (único)
      - password: senha do usuário
      - phone_number: número de celular

    Retorna:
      - JSON com mensagem de sucesso ou erro e o status HTTP correspondente.
    """
    data = request.get_json()

    # Verifica se os parâmetros necessários foram enviados
    if not data or not all(key in data for key in ['username', 'password', 'phone_number']):
        return jsonify({"error": "Parâmetros obrigatórios ausentes."}), 400

    username = data['username']
    password = data['password']
    phone_number = data['phone_number']

    # Verifica se o usuário já existe
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "O nome de usuário já existe."}), 400

    # Cria o novo usuário e define a senha com hash
    new_user = User(username=username, phone_number=phone_number)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erro ao criar usuário.", "detalhes": str(e)}), 500

    return jsonify({"message": "Usuário registrado com sucesso."}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['username', 'password']):
        return jsonify({"error": "Parâmetros obrigatórios ausentes."}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Usuário ou senha inválidos."}), 401

    # Configurar sessão com duração estendida
    access_token = create_access_token(identity=user.id)
    session['user_id'] = user.id
    session['username'] = user.username
    session['login_time'] = datetime.utcnow().isoformat()  # Para log
    session.permanent = True  # Torna a sessão permanente (usa PERMANENT_SESSION_LIFETIME)

    # Log com informações de duração
    expires_at = datetime.utcnow() + timedelta(hours=2)
    logger.info(f"✅ Login realizado - User: {username} (ID: {user.id})")
    logger.info(f"⏰ Sessão expira em: {expires_at.strftime('%d/%m/%Y %H:%M:%S')} (2 horas)")

    # Em vez de redirecionar, retorne um JSON com a URL de redirecionamento
    return jsonify({
        "success": True,
        "message": "Login realizado com sucesso",
        "redirect_url": url_for('home'),
        "session_duration": "2 horas",
        "expires_at": expires_at.isoformat()
    }), 200


@auth_bp.route('/user/balance', methods=['GET'])
def get_user_balance():
    """
    Retorna o saldo atual do usuário logado.
    Usado para atualizar saldo sem reload da página.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        balance_info = user.get_credit_balance()
        
        return jsonify({
            'success': True,
            'balance': balance_info['balance'],
            'formatted': f"R$ {balance_info['formatted']}".replace('.', ','),
            'last_updated': balance_info['last_updated']
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar saldo do usuário: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/session/check', methods=['GET'])
def check_session():
    """
    Verifica se a sessão está ativa e retorna informações.
    """
    if 'user_id' not in session:
        return jsonify({
            'authenticated': False,
            'message': 'Sessão expirada ou não autenticado'
        }), 401
    
    try:
        # Calcular tempo restante da sessão
        login_time_str = session.get('login_time')
        if login_time_str:
            login_time = datetime.fromisoformat(login_time_str)
            expires_at = login_time + timedelta(hours=2)
            time_remaining = expires_at - datetime.utcnow()
            
            if time_remaining.total_seconds() > 0:
                hours_remaining = time_remaining.total_seconds() / 3600
                return jsonify({
                    'authenticated': True,
                    'user_id': session['user_id'],
                    'username': session['username'],
                    'login_time': login_time_str,
                    'expires_at': expires_at.isoformat(),
                    'hours_remaining': round(hours_remaining, 2),
                    'message': f'Sessão ativa - {round(hours_remaining, 1)}h restantes'
                }), 200
            else:
                # Sessão expirada
                session.clear()
                return jsonify({
                    'authenticated': False,
                    'message': 'Sessão expirada'
                }), 401
        
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session['username'],
            'message': 'Sessão ativa'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar sessão: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500


@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Exemplo de rota protegida que exige um token JWT válido.

    Retorna:
      - JSON com a identidade do usuário autenticado.
    """
    current_user_id = get_jwt_identity()
    return jsonify({"message": f"Bem-vindo! Seu ID de usuário é {current_user_id}."}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout que limpa sessão.
    """
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        login_time_str = session.get('login_time')
        
        # Calcular duração da sessão
        session_duration = "N/A"
        if login_time_str:
            login_time = datetime.fromisoformat(login_time_str)
            duration = datetime.utcnow() - login_time
            hours = duration.total_seconds() / 3600
            session_duration = f"{hours:.1f}h"
        
        session.clear()
        
        logger.info(f"🚪 Logout realizado - User: {username} (ID: {user_id})")
        logger.info(f"⏱️ Duração da sessão: {session_duration}")
        
        return jsonify({
            "success": True,
            "message": "Logout realizado com sucesso",
            "session_duration": session_duration
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no logout: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500
