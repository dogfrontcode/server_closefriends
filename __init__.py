# __init__.py (na raiz do projeto)
import secrets
import logging
from flask import Flask, render_template, session, redirect, url_for
from models import db  # Aqui o Python procura pelo objeto 'db' dentro do pacote models
from flask_jwt_extended import JWTManager
from controllers import auth_bp
from controllers.credits import credits_bp

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

    db.init_app(app)
    JWTManager(app)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(credits_bp)

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
        from models.user import User
        user = User.query.get(session['user_id'])
        balance_info = user.get_credit_balance() if user else {'balance': 0, 'formatted': '0.00'}
        
        return render_template(
            "home.html",
            user_id=session.get('user_id'),
            username=session.get('username'),
            user_credits=balance_info
        )

    return app
    

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
