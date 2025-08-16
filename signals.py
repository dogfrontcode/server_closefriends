from blinker import Namespace
from models import db
from models.user import User

# Namespace para os sinais relacionados a usuários
user_signals = Namespace()
user_registered = user_signals.signal('user-registered')

@user_registered.connect
def create_user(sender, username, password, phone_number):
    """Cria um novo usuário no banco de dados.

    Levanta ValueError se o username já existir.
    """
    if User.query.filter_by(username=username).first():
        raise ValueError('O nome de usuário já existe.')

    new_user = User(username=username, phone_number=phone_number)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

    return new_user
