from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/microf_dev')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    bcrypt.init_app(app)
    
    # Importation des modèles
    from app.models import Tenant, User
    
    # Importation des blueprints
    from app.routes import auth, dashboard, clients, products, credit_requests, contracts, reports, holidays, groups, cash, savings, users
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(credit_requests.bp)
    app.register_blueprint(contracts.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(holidays.bp)
    app.register_blueprint(groups.bp)
    app.register_blueprint(cash.bp)
    app.register_blueprint(savings.bp)
    app.register_blueprint(users.bp)


    @app.route('/')
    def home():
        return render_template('index.html')

    # Context processor pour les variables globales
    @app.context_processor
    def inject_global_data():
        from datetime import datetime
        citations = [
            "💪 Le succès, c'est tomber sept fois et se relever huit fois.",
            "🌟 La meilleure façon de prédire l'avenir est de le créer.",
            "🐦 Petit à petit, l'oiseau fait son nid.",
            "🤝 L'union fait la force.",
            "🚀 Chaque grand voyage commence par un premier pas.",
            "⏳ La patience est l'art d'espérer.",
            "💡 Ce n'est pas parce que les choses sont difficiles que nous n'osons pas, c'est parce que nous n'osons pas qu'elles sont difficiles.",
            "📈 Investir dans les autres, c'est investir dans son propre avenir.",
            "🎯 La discipline est le pont entre les objectifs et l'accomplissement.",
            "💖 La confiance est le ciment d'une relation durable."
        ]
        return {
            'current_year': datetime.now().year,
            'today_citation': citations[datetime.now().day % len(citations)]
        }
    
    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(user_id)