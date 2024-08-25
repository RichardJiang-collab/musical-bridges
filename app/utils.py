from .models import Song, Playlist
import random
from sqlalchemy import func
from .extensions import db

def get_random_tracks(emotion, min_count=10, max_count=20):
    tracks = Song.query.filter_by(emotion=emotion).order_by(func.random()).limit(max_count).all()
    
    if len(tracks) < min_count:
        return None  # Not enough tracks found
    
    return random.sample(tracks, random.randint(min_count, min(len(tracks), max_count)))

def calculate_composite_score(track):
    # Calculate a composite score based on all features
    return (
        track.danceability * 0.1 +
        track.energy * 0.1 +
        track.loudness * 0.05 +
        track.speechiness * 0.05 +
        track.acousticness * 0.1 +
        track.instrumentalness * 0.1 +
        track.liveness * 0.05 +
        track.valence * 0.1 +
        track.tempo * 0.05 +
        track.popularity * 0.3  # Give more weight to popularity
    )

def get_top_recommended_tracks(playlist_id, limit=5):
    playlist = db.session.get(Playlist, playlist_id)
    if not playlist:
        return []
    return sorted(playlist.songs, key=lambda x: x.popularity, reverse=True)[:limit]