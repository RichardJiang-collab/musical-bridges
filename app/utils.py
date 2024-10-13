import spotipy, random
from flask import current_app, session
from .models import Song, Emotion

POPULAR_GENRES = [
    'pop', 'hip-hop', 'jazz', 'rock', 'electronic', 'classical', 'blues', 'latin', 'reggae', 'soul'
]

def get_spotify_client(access_token=None):
    if not access_token:
        if 'token_info' not in session:
            current_app.logger.error("No token info in session")
            return None
        access_token = session['token_info']['access_token']

    return spotipy.Spotify(auth=access_token)

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

    user_genres = session.get('selectedGenres', [])
    random_genres = random.sample(POPULAR_GENRES, k=3)
    combined_genres = list(set(user_genres + random_genres))  # Combining user and random genres

    if len(user_genres) > 5:
        combined_genres = list(set(random.sample(user_genres, 5)))
    elif len(combined_genres) > 5:
        combined_genres = list(set(random.sample(combined_genres, 5)))

    attributes = emotion_to_attributes.get(emotion, {})
    try:
        results = sp.recommendations(limit=max_count, seed_genres=combined_genres, **attributes)
    except Exception as e:
        print(f"Error fetching recommendations: {str(e)}")
        return []
    if len(results.get('tracks', [])) < min_count:
        return []

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

    if not tracks:  # Ensure there are tracks to add
        print("No tracks provided to create a playlist")
        return None

    try:
        user_id = sp.me()['id']
        playlist = sp.user_playlist_create(user_id, "Emotion-based Playlist", public=False)
        track_uris = [f"spotify:track:{track.spotify_id}" for track in tracks]
        sp.playlist_add_items(playlist['id'], track_uris)
    except Exception as e:
        print(f"Error creating playlist: {str(e)}")
        return None

    return playlist['id']


# Create Embedded Code
def get_embedded_playlist_code(playlist_id):
    return f'<iframe src="https://open.spotify.com/embed/playlist/{playlist_id}" width="100%" height="808" frameborder="0" allowtransparency="true" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'

def get_embedded_track_code(track_id):
    return f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="300" height="380" frameborder="0" allowfullscreen="" allowtransparency="true" allow="encrypted-media"></iframe>'

def calculate_composite_score(track):
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

    try:
        playlist_tracks = sp.playlist_tracks(playlist_id)
        track_ids = [item['track']['id'] for item in playlist_tracks['items']]
        audio_features = sp.audio_features(track_ids)
    except Exception as e:
        print(f"Error fetching playlist tracks or audio features: {str(e)}")
        return []

    tracks = []
    for item, features in zip(playlist_tracks['items'], audio_features):
        if features:
            tracks.append(Song(
                spotify_id=item['track']['id'],
                title=item['track']['name'],
                artist=item['track']['artists'][0]['name'],
                album=item['track']['album']['name'],
                popularity=item['track']['popularity'],
                danceability=features.get('danceability', 0),
                energy=features.get('energy', 0),
                loudness=features.get('loudness', 0),
                speechiness=features.get('speechiness', 0),
                acousticness=features.get('acousticness', 0),
                instrumentalness=features.get('instrumentalness', 0),
                liveness=features.get('liveness', 0),
                valence=features.get('valence', 0),
                tempo=features.get('tempo', 0)
            ))

    sorted_tracks = sorted(tracks, key=calculate_composite_score, reverse=True)
    return sorted_tracks[:limit]