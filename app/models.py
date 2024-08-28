from .extensions import db
from enum import Enum

class Emotion(Enum):
    SAD_NORMAL = 'SAD_NORMAL'
    SAD_INTENSE = 'SAD_INTENSE'
    ANGRY_NORMAL = 'ANGRY_NORMAL'
    ANGRY_INTENSE = 'ANGRY_INTENSE'

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

playlist_songs = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)

Song.playlists = db.relationship('Playlist', secondary='playlist_songs', back_populates='songs')