# __init__.py (na raiz do projeto)
import secrets
import logging
from flask import Flask, render_template, session, redirect, url_for
try:
    # Tenta imports relativos (quando usado como módulo)
    from .models import db
    from .controllers import auth_bp
    from .controllers.credits import credits_bp
    from .controllers.cnh import cnh_bp
    from .controllers.pix_payment import pix_bp
    from .apitest.cnh_test import cnh_test_bp
    from .models.user import User
    from .models.credit_transaction import CreditTransaction
    from .models.cnh_request import CNHRequest
except ImportError:
    # Fallback para imports absolutos (quando executado diretamente)
    from models import db
    from controllers import auth_bp
    from controllers.credits import credits_bp
    from controllers.cnh import cnh_bp
    from controllers.pix_payment import pix_bp
    from apitest.cnh_test import cnh_test_bp
    from models.user import User
    from models.credit_transaction import CreditTransaction
    from models.cnh_request import CNHRequest

from flask_jwt_extended import JWTManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Gera uma chave JWT segura dinamicamente a cada inicialização.
    app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    
    # ⏰ Configurações de sessão melhoradas - 2 HORAS de duração
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 2 horas
    app.config['SESSION_COOKIE_SECURE'] = False  # True apenas em HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Proteção XSS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Proteção CSRF
    app.config['SESSION_COOKIE_MAX_AGE'] = 7200  # 2 horas em segundos (2 * 60 * 60)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Renova a sessão a cada request

    db.init_app(app)
    JWTManager(app)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(credits_bp)
    app.register_blueprint(cnh_bp)
    app.register_blueprint(pix_bp)  # Registrar blueprint PIX
    app.register_blueprint(cnh_test_bp)  # Registrar blueprint de testes CNH

    with app.app_context():
        db.create_all()

    # Define a rota para a raiz da aplicação que renderiza o index.html
    @app.route("/")
    def index():
        return render_template("index.html")
    
    # Define a rota do dashboard, que utiliza os dados da sessão
    @app.route("/home")
    def home():
        if 'user_id' not in session:
            return redirect(url_for('index'))
        
        # Buscar informações do usuário incluindo créditos
        # User já foi importado no topo do arquivo
        user = User.query.get(session['user_id'])
        balance_info = user.get_credit_balance() if user else {'balance': 0, 'formatted': '0.00'}
        
        return render_template(
            "home.html",
            user_id=session.get('user_id'),
            username=session.get('username'),
            user_credits=balance_info
        )

    @app.route("/cnh/form")
    def cnh_form():
        if 'user_id' not in session:
            return redirect(url_for('index'))

        user = User.query.get(session['user_id'])
        balance_info = user.get_credit_balance() if user else {'balance': 0, 'formatted': '0.00'}

        return render_template(
            "cnh_form.html",
            user_id=session.get('user_id'),
            username=session.get('username'),
            user_credits=balance_info
        )

    @app.route("/cnhs")
    def cnhs():
        if 'user_id' not in session:
            return redirect(url_for('index'))

        user = User.query.get(session['user_id'])
        balance_info = user.get_credit_balance() if user else {'balance': 0, 'formatted': '0.00'}

        return render_template(
            "cnhs.html",
            user_id=session.get('user_id'),
            username=session.get('username'),
            user_credits=balance_info
        )

    @app.route("/credits")
    def credits():
        if 'user_id' not in session:
            return redirect(url_for('index'))

        user = User.query.get(session['user_id'])
        balance_info = user.get_credit_balance() if user else {'balance': 0, 'formatted': '0.00'}

        return render_template(
            "credits.html",
            user_id=session.get('user_id'),
            username=session.get('username'),
            user_credits=balance_info
        )

    @app.route("/profile")
    def profile():
        if 'user_id' not in session:
            return redirect(url_for('index'))

        user = User.query.get(session['user_id'])
        balance_info = user.get_credit_balance() if user else {'balance': 0, 'formatted': '0.00'}

        return render_template(
            "profile.html",
            user_id=session.get('user_id'),
            username=session.get('username'),
            user_credits=balance_info
        )

    return app
    

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
