from flask import current_app, session
from .models import Song, Emotion
import spotipy, random, os

random.seed(42)
ALL_GENRES = []

def init_app(app):
    return os.path.join(app.static_folder, 'genres.md')

#* Defining the attributes for each emotion
emotion_to_attributes = {
    Emotion.JOY: {
        # Strict/target values:
        "danceability": 0.80,    # target: ≥0.80
        "energy": 0.80,          # target: ≥0.80
        "instrumentalness": 0.20,  # target: ≤0.20
        "liveness": 0.20,        # target: ≤0.20
        "loudness": -7,          # target (dB): around -7 dB (closer to 0 = louder)
        "mode": 1,               # 1 = major
        "tempo": 130,            # target BPM
        "acousticness": (0.1, 0.3),
        "time_signature": 4,     # most tracks in 4/4 time
        "valence_range": (0.7, 1.0)
    },
    Emotion.TENDER: {
        "danceability": 0.40,    # target: ~0.40
        "energy": 0.30,          # target: ~0.30
        "instrumentalness": 0.30,  # target: ~0.30 (may vary with vocal/instrumental balance)
        "liveness": 0.20,        # target: ≤0.20
        "loudness": -20,         # target (dB): around -20 dB (softer)
        "mode": 1,               # major
        "tempo": 70,             # target BPM
        "acousticness": (0.6, 0.9),
        "time_signature": 4,
        "valence_range": (0.5, 0.7)
    },
    Emotion.ANGER: {
        "danceability": 0.55,    # target: ~0.55
        "energy": 0.85,          # target: ≥0.85 (very high)
        "instrumentalness": 0.20,  # target: ≤0.20
        "liveness": 0.40,        # target: around 0.40 (some live/rough feel)
        "loudness": -6,          # target (dB): around -6 dB (very loud)
        "mode": 0,               # 0 = minor
        "tempo": 140,            # target BPM
        "acousticness": (0.0, 0.3),
        "time_signature": 4,
        "valence_range": (0.0, 0.3)
    },
    Emotion.SADNESS: {
        "danceability": 0.30,    # target: ~0.30
        "energy": 0.30,          # target: ~0.30 (low energy)
        "instrumentalness": 0.20,  # target: ≤0.20
        "liveness": 0.20,        # target: ≤0.20
        "loudness": -20,         # target (dB): around -20 dB (soft)
        "mode": 0,               # minor
        "tempo": 60,             # target BPM
        "acousticness": (0.4, 0.7),
        "time_signature": 4,
        "valence_range": (0.0, 0.3)
    }
}

#* 1. Check if the user have access token or not for Spotify Access
def get_spotify_client(access_token=None):
    if not access_token:
        if 'token_info' not in session:
            current_app.logger.error("No token info in session")
            return None
        access_token = session['token_info']['access_token']
    return spotipy.Spotify(auth=access_token)


#* 2. Get tracks from Spotify based on the user's selected genres and the emotion
def get_random_tracks(emotion, min_count=10, max_count=20):
    sp = get_spotify_client()
    if not sp:
        raise Exception("Spotify client not authenticated")

    # Load genres (unchanged)
    GENRES_PATH = current_app.config['GENRES_PATH']
    ALL_GENRES = []
    with open(GENRES_PATH, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            if line.strip() and line.strip()[0].isdigit():
                genre = line.strip().split('. ', 1)[1]
                ALL_GENRES.append(genre)

    # Combine user and random genres
    user_genres = session.get('selectedGenres', [])
    random_genres = random.sample(ALL_GENRES, k=3)
    combined_genres = list(set(user_genres + random_genres))

    # Map emotion to keyword
    emotion_map = {
        Emotion.JOY: "happy",
        Emotion.TENDER: "chill",
        Emotion.ANGER: "intense",
        Emotion.SADNESS: "sad"
    }
    emotion_keyword = emotion_map.get(emotion, "happy")  # Default to "happy"
    selected_genre = random.choice(user_genres if user_genres else combined_genres)

    try:
        # Search for playlists
        query = f"{emotion_keyword} {selected_genre}"
        results = sp.search(q=query, type='playlist', limit=5)
        if not results or not results['playlists']['items']: #check if results or items exist.
            return []

        # Fetch tracks from the first playlist
        playlist_id = results['playlists']['items'][0]['id']
        playlist_results = sp.playlist_tracks(playlist_id)
        if not playlist_results or not playlist_results['items']: #check if playlist_results or items exist.
            return []
        all_tracks = playlist_results['items']

        # Select tracks
        if len(all_tracks) < min_count:
            return []
        selected_tracks = random.sample(all_tracks, k=min(max_count, len(all_tracks)))

        # Parse into Song objects
        song_objects = []
        for item in selected_tracks:
            if item and item['track'] and item['track']['id']: # Check that item, track, and track id exist.
                song_objects.append(Song(
                    spotify_id=item['track']['id'],
                    title=item['track']['name'],
                    artist=item['track']['artists'][0]['name'],
                    album=item['track']['album']['name'],
                    popularity=item['track']['popularity'],
                    emotion=emotion
                ))
        return song_objects

    except Exception as e:
        print(f"Error fetching tracks: {str(e)}")
        return []


#* 3. Function for creating a Spotify playlist
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


#* 4. Create Embedded Codes for the curated playlist and the top 5 tracks
def get_embedded_playlist_code(playlist_id):
    return f'<iframe src="https://open.spotify.com/embed/playlist/{playlist_id}" width="100%" height="808" frameborder="0" allowtransparency="true" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'
def get_embedded_track_code(track_id):
    return f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="300" height="380" frameborder="0" allowfullscreen="" allowtransparency="true" allow="encrypted-media"></iframe>'


#* 5. Defining each metric's weight in the overall recommendation of the song
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


#* 6. Recommend top 5 tracks
def get_top_recommended_tracks(playlist_id, limit=5):
    sp = get_spotify_client()
    if not sp:
        raise Exception("Spotify client not authenticated")

    try:
        playlist_tracks = sp.playlist_tracks(playlist_id)
        tracks = [Song(
            spotify_id=item['track']['id'],
            title=item['track']['name'],
            artist=item['track']['artists'][0]['name'],
            album=item['track']['album']['name'],
            popularity=item['track']['popularity']
        ) for item in playlist_tracks['items']]

        # Sort by popularity
        sorted_tracks = sorted(tracks, key=lambda track: track.popularity, reverse=True)
        return sorted_tracks[:limit]
    except Exception as e:
        print(f"Error fetching playlist tracks: {str(e)}")
        return []