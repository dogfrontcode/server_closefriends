# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Cria a instância do SQLAlchemy para ser utilizada em todo o pacote models
db = SQLAlchemy()

# Importar todos os modelos
from .user import User
from .credit_transaction import CreditTransaction
from .cnh_request import CNHRequest
