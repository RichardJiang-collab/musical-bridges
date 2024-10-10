import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'your_database.db')).replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Spotify API credentials
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI', 'https://musical-bridges-063243932240.herokuapp.com/callback')

    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # Pagination settings
    SONGS_PER_PAGE = 20

    # Playlist settings
    MIN_PLAYLIST_TRACKS = 10
    MAX_PLAYLIST_TRACKS = 20

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name='default'):
    return config.get(config_name, DevelopmentConfig)
