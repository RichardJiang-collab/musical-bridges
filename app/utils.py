from spotipy.oauth2 import SpotifyOAuth
import spotipy
from flask import current_app, session
from .models import Song, Emotion

def get_spotify_client():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = SpotifyOAuth(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
        scope="playlist-modify-private",
        cache_handler=cache_handler
    )
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return None
    return spotipy.Spotify(auth_manager=auth_manager)

def get_random_tracks(emotion, min_count=10, max_count=20):
    sp = get_spotify_client()
    if not sp:
        raise Exception("Spotify client not authenticated")

    emotion_to_attributes = {
        Emotion.SAD_INTENSE: {"valence": "0.0-0.3", "energy": "0.7-1.0"},
        Emotion.SAD_NORMAL: {"valence": "0.0-0.3", "energy": "0.0-0.3"},
        Emotion.ANGRY_INTENSE: {"valence": "0.0-0.4", "energy": "0.8-1.0"},
        Emotion.ANGRY_NORMAL: {"valence": "0.0-0.4", "energy": "0.4-0.7"},
    }

    attributes = emotion_to_attributes.get(emotion, {})
    
    results = sp.recommendations(limit=max_count, seed_genres=['pop'], **attributes)
    
    if len(results['tracks']) < min_count:
        return None

    return [Song(
        spotify_id=track['id'],
        title=track['name'],
        artist=track['artists'][0]['name'],
        album=track['album']['name'],
        popularity=track['popularity'],
        emotion=emotion
    ) for track in results['tracks']]

def create_spotify_playlist(tracks):
    sp = get_spotify_client()
    if not sp:
        raise Exception("Spotify client not authenticated")

    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, "Emotion-based Playlist", public=False)

    track_uris = [f"spotify:track:{track.spotify_id}" for track in tracks]
    sp.playlist_add_items(playlist['id'], track_uris)

    return playlist['id']

def get_embedded_playlist_code(playlist_id):
    return f'<iframe src="https://open.spotify.com/embed/playlist/{playlist_id}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'

def get_embedded_track_code(track_id):
    return f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'


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
    sp = get_spotify_client()
    if not sp:
        raise Exception("Spotify client not authenticated")

    playlist_tracks = sp.playlist_tracks(playlist_id)
    track_ids = [item['track']['id'] for item in playlist_tracks['items']]

    # Fetch audio features for all tracks in one API call
    audio_features = sp.audio_features(track_ids)

    tracks = []
    for item, features in zip(playlist_tracks['items'], audio_features):
        if features:  # Sometimes features might be None for certain tracks
            tracks.append(Song(
                spotify_id=item['track']['id'],
                title=item['track']['name'],
                artist=item['track']['artists'][0]['name'],
                album=item['track']['album']['name'],
                popularity=item['track']['popularity'],
                danceability=features['danceability'],
                energy=features['energy'],
                loudness=features['loudness'],
                speechiness=features['speechiness'],
                acousticness=features['acousticness'],
                instrumentalness=features['instrumentalness'],
                liveness=features['liveness'],
                valence=features['valence'],
                tempo=features['tempo']
            ))

    # Sort tracks by composite score
    sorted_tracks = sorted(tracks, key=calculate_composite_score, reverse=True)
    return sorted_tracks[:limit]