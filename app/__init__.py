#  Archivo de inicialización del módulo de la aplicación.
#  Aquí se configura la aplicación y se registran las rutas y extensiones
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'renovate.login'

    from app import models

    from app.routes import bp
    app.register_blueprint(bp)

    return app
