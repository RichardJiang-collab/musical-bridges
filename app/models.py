from .extensions import db
from enum import Enum
from datetime import datetime, timezone

#* Defining Classes
class Emotion(Enum):
    JOY = 'JOY'
    TENDER = 'TENDER'
    ANGER = 'ANGER'
    SADNESS = 'SADNESS'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100)) # Add this line
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    expires_at = db.Column(db.Integer)
    genres = db.relationship('UserGenre', backref='user', lazy=True)

    def __init__(self, user_id, display_name=None): # Update this line
        self.user_id = user_id
        self.display_name = display_name # Add this line

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

class UserGenre(db.Model):
    __tablename__ = 'user_genres'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.user_id'), nullable=False)
    genre = db.Column(db.String, nullable=False)

    def __init__(self, user_id, genre):
        self.user_id = user_id
        self.genre = genre

class SavedTopSongsLinks(db.Model):
    __tablename__ = 'saved_top_songs_links'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.user_id'), nullable=False)
    top_songs_links = db.Column(db.Text, nullable=False)

    def __init__(self, user_id, top_songs_links):
        self.user_id = user_id
        self.top_songs_links = top_songs_links

# Playlist-Songs
playlist_songs = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)
Song.playlists = db.relationship('Playlist', secondary='playlist_songs', back_populates='songs')