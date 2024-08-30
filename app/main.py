from flask import Blueprint, request, jsonify, current_app, redirect, session, url_for
from .models import Emotion
from .utils import get_random_tracks, get_top_recommended_tracks, create_spotify_playlist, get_embedded_playlist_code, get_embedded_track_code
from spotipy.oauth2 import SpotifyOAuth

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "Welcome to the Music Recommendation System! <a href='/login'>Login with Spotify</a>"

@main.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
        scope="playlist-modify-private"
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@main.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
        scope="playlist-modify-private"
    )
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for('main.create_playlist_form'))

@main.route('/create_playlist_form')
def create_playlist_form():
    if 'token_info' not in session:
        return redirect(url_for('main.login'))
    return '''
        <form action="/api/create_playlist" method="post">
            <label for="emotion">Emotion:</label>
            <input type="text" id="emotion" name="emotion" required><br><br>
            <label for="intensity">Intensity:</label>
            <input type="text" id="intensity" name="intensity" required><br><br>
            <input type="submit" value="Create Playlist">
        </form>
    '''

@main.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    if 'token_info' not in session:
        print("No token_info in session, redirecting to login")
        return redirect(url_for('main.login'))

    emotion = request.form.get('emotion')
    intensity = request.form.get('intensity')
    print(f"Received emotion: {emotion}, intensity: {intensity}")

    if not emotion or not intensity:
        print("Emotion or intensity missing")
        return jsonify({'error': 'Emotion and intensity are required'}), 400

    try:
        emotion_key = f"{emotion.upper()}_{intensity.upper()}"
        print(f"Constructed emotion key: {emotion_key}")

        if emotion_key not in Emotion.__members__:
            print(f"Invalid emotion key: {emotion_key}")
            return jsonify({'error': 'Invalid emotion or intensity'}), 400

        emotion_enum = Emotion[emotion_key]
        print(f"Emotion enum: {emotion_enum}")

        tracks = get_random_tracks(emotion_enum)
        print(f"Tracks returned by get_random_tracks: {len(tracks) if tracks else 0}")

        if not tracks:
            print("No tracks found for the given emotion")
            return jsonify({'error': f'No tracks found for emotion: {emotion_key}'}), 404


        # IMPORTANT: Spotify_Playlist_Ids and Top 5 Tracks Ids links

        spotify_playlist_id = create_spotify_playlist(tracks)
        print(f"Created Spotify playlist with ID: {spotify_playlist_id}")

        embedded_playlist_code = get_embedded_playlist_code(spotify_playlist_id)
        print("Generated embedded playlist code")

        top_tracks = get_top_recommended_tracks(spotify_playlist_id)
        print(f"Got {len(top_tracks)} top recommended tracks")

        top_tracks_embedded = [get_embedded_track_code(track.spotify_id) for track in top_tracks]
        print("Generated embedded codes for top tracks")

        print("\n--- Embedded Playlist Code ---")
        print(embedded_playlist_code)

        print("\n--- Top 5 Recommended Tracks Embedded Codes ---")
        for i, embedded_code in enumerate(top_tracks_embedded, 1):
            print(f"\n{i}. Embedded Code:")
            print(embedded_code)

        return jsonify({
            'message': 'Playlist created successfully', 
            'spotify_playlist_id': spotify_playlist_id,
            'embedded_playlist_code': embedded_playlist_code,
            'top_tracks_embedded': top_tracks_embedded
        }), 201
    except Exception as e:
        error_msg = f"Error in create_playlist: {str(e)}"
        current_app.logger.error(error_msg)
        print(error_msg)
        return jsonify({'error': error_msg}), 500

@main.route('/api/recommend_top_tracks/<string:playlist_id>', methods=['GET'])
def recommend_top_tracks(playlist_id):
    try:
        top_tracks = get_top_recommended_tracks(playlist_id)

        tracks_data = [{
            'id': track.spotify_id,
            'title': track.title,
            'artist': track.artist,
            'album': track.album,
            'popularity': track.popularity,
            'embedded_track_code': get_embedded_track_code(track.spotify_id)
        } for track in top_tracks]

        return jsonify({'top_tracks': tracks_data}), 200
    except Exception as e:
        error_msg = f"Error in recommend_top_tracks: {str(e)}"
        current_app.logger.error(error_msg)
        print(error_msg)
        return jsonify({'error': error_msg}), 500