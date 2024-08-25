from flask import Flask
from .extensions import db, migrate
from .main import main as main_blueprint
from .models import Song, Playlist, Emotion  # Add this line

def create_app(config_name='testing'):
    app = Flask(__name__)

    # Load configuration
    config_module = 'app.config'
    try:
        if config_name == 'testing':
            app.config.from_object(f'{config_module}.TestingConfig')
        else:
            app.config.from_object(f'{config_module}.Config')
    except ImportError as e:
        raise ImportError(f"Could not import configuration '{config_name}'. Error: {e}")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(main_blueprint)

    return app