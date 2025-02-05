# __init__.py (na raiz do projeto)
import secrets
from flask import Flask, render_template , session
from models import db  # Aqui o Python procura pelo objeto 'db' dentro do pacote models
from flask_jwt_extended import JWTManager
from controllers import auth_bp

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Gera uma chave JWT segura dinamicamente a cada inicialização.
    app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
    app.config['SECRET_KEY'] = secrets.token_hex(16)

    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp)

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
        return render_template(
            "home.html",
            user_id=session.get('user_id'),
            username=session.get('username')
        )

    return app
    

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
