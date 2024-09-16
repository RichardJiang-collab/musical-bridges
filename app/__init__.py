import os
from flask import Flask, send_from_directory
from .extensions import db, migrate
from .main import main as main_blueprint
from flask_cors import CORS

def create_app(config_name='production'):
    # Set up paths to the static folder
    base_dir = os.path.abspath(os.path.dirname(__file__))
    static_folder = os.path.join(base_dir, '..', 'webflow_exporter_base')

    print(f"Base directory: {base_dir}")
    print(f"Static folder path: {static_folder}")
    print(f"Static folder exists: {os.path.exists(static_folder)}")
    print(f"Contents of static folder: {os.listdir(static_folder)}")

    app = Flask(__name__, instance_relative_config=True, static_folder=static_folder, static_url_path='')
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    app.secret_key = os.environ.get('SECRET_KEY') or 'your-secret-key'
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(main_blueprint)
    with app.app_context():
        db.create_all()
    return app