# controllers/__init__.py
from flask import Blueprint

# Cria o blueprint para as rotas de autenticação com prefixo /api
auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# Importa os módulos que definem as rotas, garantindo que elas sejam registradas
from . import auth

# Importa o blueprint de créditos
from .credits import credits_bp
