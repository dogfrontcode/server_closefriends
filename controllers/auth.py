# controllers/auth.py
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from models import db
from . import auth_bp

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
    """
    Autentica um usuário e gera um token JWT.

    Requer um payload JSON com os parâmetros:
      - username: nome de usuário
      - password: senha do usuário

    Retorna:
      - JSON contendo o token de acesso ou mensagem de erro com o status HTTP correspondente.
    """
    data = request.get_json()
    
    # Verifica se os parâmetros necessários foram enviados
    if not data or not all(key in data for key in ['username', 'password']):
        return jsonify({"error": "Parâmetros obrigatórios ausentes."}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Usuário ou senha inválidos."}), 401

    # Cria o token JWT usando o ID do usuário como identidade
    access_token = create_access_token(identity=user.id)
    return jsonify({"access_token": access_token}), 200

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
