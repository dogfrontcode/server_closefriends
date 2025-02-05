# models/user.py
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """
    Modelo que representa um usuário no banco de dados.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        """
        Define a senha do usuário armazenando-a como hash.
        :param password: senha em texto plano
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifica se a senha fornecida confere com o hash armazenado.
        :param password: senha em texto plano
        :return: True se a senha estiver correta; False caso contrário.
        """
        return check_password_hash(self.password_hash, password)
