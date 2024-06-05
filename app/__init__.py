#  Archivo de inicialización del módulo de la aplicación.
#  Aquí se configura la aplicación y se registran las rutas y extensiones
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app import routes, models  # Importar modelos para que estén registrados con SQLAlchemy
    app.register_blueprint(routes.bp)

    return app
