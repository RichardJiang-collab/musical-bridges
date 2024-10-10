import os
from flask import Flask
from .extensions import db, migrate
from .main import main as main_blueprint
from flask_cors import CORS
from whitenoise import WhiteNoise
# from flask_session import Session  # Uncomment if using Flask-Session
def create_app(config_name='production'):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    static_folder = os.path.join(base_dir, '..', 'webflow_exporter_base')

    app = Flask(__name__, instance_relative_config=True, static_folder=static_folder, static_url_path='/static')
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Initialize WhiteNoise
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_folder, prefix='static/')

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