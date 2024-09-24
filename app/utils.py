from spotipy.oauth2 import SpotifyOAuth
import spotipy
from flask import current_app, session
import time
from .models import Song, Emotion

def get_spotify_client(access_token=None):
    if not access_token:
        if 'token_info' not in session:
            current_app.logger.error("No token info in session")
            return None
        access_token = session['token_info']['access_token']

    return spotipy.Spotify(auth=access_token)

# Get tracks based on the each emotion & intensity music data configurations
def get_random_tracks(emotion, min_count=10, max_count=20):
    sp = get_spotify_client()
    if not sp:
        raise Exception("Spotify client not authenticated")

    emotion_to_attributes = {
        Emotion.SAD_INTENSE: {"valence": "0.6-1.0", "energy": "0.7-1.0"},
        Emotion.SAD_NORMAL: {"valence": "0.6-1.0", "energy": "0.0-0.3"},
        Emotion.ANGRY_INTENSE: {"valence": "0.5-0.8", "energy": "0.8-1.0"},
        Emotion.ANGRY_NORMAL: {"valence": "0.5-0.8", "energy": "0.4-0.7"},
    }

    attributes = emotion_to_attributes.get(emotion, {})
    
    results = sp.recommendations(limit=max_count, seed_genres=['rock'], **attributes)
    
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

# Create the recommended playlist based on the songs we have get from "get_random_tracks" function
def create_spotify_playlist(tracks):
    # Use the Spotify API to create the playlist
    sp = get_spotify_client()
    if not sp:
        raise Exception("Spotify client not authenticated")

    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, "Emotion-based Playlist", public=False)

    track_uris = [f"spotify:track:{track.spotify_id}" for track in tracks]
    sp.playlist_add_items(playlist['id'], track_uris)

    return playlist['id']

# Create Embedded Code
def get_embedded_playlist_code(playlist_id):
    return f'<iframe src="https://open.spotify.com/embed/playlist/{playlist_id}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'

def get_embedded_track_code(track_id):
    return f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'

# Algorithm (weights for each music feature when picking each Songs)
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

# Use the composite_score function to pick the top 5 recommended tracks
def get_top_recommended_tracks(playlist_id, limit=5):
    # Use Spotify API to pick the top 5 recommended tracks
    sp = get_spotify_client()

    # Error handling
    if not sp:
        raise Exception("Spotify client not authenticated")

    playlist_tracks = sp.playlist_tracks(playlist_id)
    track_ids = [item['track']['id'] for item in playlist_tracks['items']]

    # Fetch audio features for all tracks in one API call
    audio_features = sp.audio_features(track_ids)

    # Add tracks to the Song Model
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
    return sorted_tracks[:limit]  # return the top 5 tracks