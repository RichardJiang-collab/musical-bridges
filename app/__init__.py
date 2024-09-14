import os
from flask import Flask, send_from_directory
from .extensions import db, migrate
from .main import main as main_blueprint
from flask_cors import CORS

def create_app(config_name='development'):
    # Set up paths to the static folder
    base_dir = os.path.abspath(os.path.dirname(__file__))
    static_folder = os.path.join(base_dir, '..', 'webflow_exporter_base')  # Go up one directory and then into webflow_exporter_base

    app = Flask(__name__, instance_relative_config=True, template_folder='templates', static_folder=static_folder)
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(main_blueprint)
    with app.app_context():
        db.create_all()
    return app