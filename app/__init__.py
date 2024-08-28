import os
from flask import Flask
from .extensions import db, migrate
from .main import main as main_blueprint

def create_app(config_name='development'):
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(main_blueprint)

    # Initialize database within app context
    with app.app_context():
        db.create_all()

    return app