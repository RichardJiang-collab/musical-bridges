from .extensions import db
from enum import Enum

class Emotion(Enum):
    SAD_NORMAL = 'SAD_NORMAL'
    SAD_INTENSE = 'SAD_INTENSE'
    ANGRY_NORMAL = 'ANGRY_NORMAL'
    ANGRY_INTENSE = 'ANGRY_INTENSE'

from .extensions import db
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = 'users'

    # Primary key, unique identifier for each user
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Unique user ID, can be a random number or a Spotify user ID
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    genres = db.relationship('UserGenre', backref='user', lazy=True)

    def __init__(self, user_id):
        self.user_id = user_id


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    album = db.Column(db.String(100))
    spotify_id = db.Column(db.String(100), unique=True, nullable=False)
    emotion = db.Column(db.Enum(Emotion), nullable=False)
    danceability = db.Column(db.Float, nullable=False)
    energy = db.Column(db.Float, nullable=False)
    key = db.Column(db.String(10), nullable=False)
    loudness = db.Column(db.Float, nullable=False)
    mode = db.Column(db.String(10), nullable=False)
    speechiness = db.Column(db.Float, nullable=False)
    acousticness = db.Column(db.Float, nullable=False)
    instrumentalness = db.Column(db.Float, nullable=False)
    liveness = db.Column(db.Float, nullable=False)
    valence = db.Column(db.Float, nullable=False)
    tempo = db.Column(db.Float, nullable=False)
    duration_ms = db.Column(db.Integer, nullable=False)
    popularity = db.Column(db.Integer, nullable=False)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    emotion = db.Column(db.Enum(Emotion), nullable=False)
    songs = db.relationship('Song', secondary='playlist_songs', back_populates='playlists')

# Playlist-Songs
playlist_songs = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)
Song.playlists = db.relationship('Playlist', secondary='playlist_songs', back_populates='songs')

class UserGenre(db.Model):
    __tablename__ = 'user_genres'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.user_id'), nullable=False)
    genre = db.Column(db.String, nullable=False)

    def __init__(self, user_id, genre):
        self.user_id = user_id
        self.genre = genre