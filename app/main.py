from flask import Blueprint, request, jsonify, current_app, redirect, session, url_for, render_template, send_from_directory
from .models import Emotion
from .utils import get_random_tracks, get_top_recommended_tracks, create_spotify_playlist, get_embedded_playlist_code, get_embedded_track_code, get_spotify_client
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
import time

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

@main.route('/')
def index():
    current_app.logger.info(f"Session: {session}")
    if 'token_info' not in session:
        current_app.logger.info("No token_info in session, redirecting to login")
        return redirect(url_for('main.login'))
    try:
        current_app.logger.info(f"Static folder: {current_app.static_folder}")
        return send_from_directory(current_app.static_folder, 'index.html')
    except Exception as e:
        current_app.logger.error(f"Error serving index.html: {str(e)}")
        return f"Error serving the home page: {str(e)}", 500
    
@main.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
        scope="playlist-modify-private"
    )
    auth_url = sp_oauth.get_authorize_url()
    return render_template('login.html', auth_url=auth_url)

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
    current_app.logger.info(f"Token info stored in session: {token_info}")
    return redirect(url_for('main.index'))

@main.route('/emotions')
def emotions():
    if 'token_info' not in session:
        return redirect(url_for('main.login'))
    return send_from_directory(current_app.static_folder, 'emotions.html')

@main.route('/anger-selection')
def anger_selection():
    if 'token_info' not in session:
        return redirect(url_for('main.login'))
    return send_from_directory(current_app.static_folder, 'anger-selection.html')

@main.route('/sadness-selection')
def sadness_selection():
    if 'token_info' not in session:
        return redirect(url_for('main.login'))
    return send_from_directory(current_app.static_folder, 'sadness-selection.html')

@main.route('/recommendations')
def recommendations():
    if 'token_info' not in session:
        return redirect(url_for('main.login'))
    return send_from_directory(current_app.static_folder, 'recommendations.html')

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = SpotifyOAuth(client_id=current_app.config['SPOTIFY_CLIENT_ID'],
                                client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
                                redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
                                scope="playlist-modify-private")
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info

@main.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    token_info = get_token()
    if not token_info:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_app.logger.info(f"Received request: {request.json}")
    
    try:
        sp = get_spotify_client()
        if not sp:
            return jsonify({'error': 'Spotify client not authenticated'}), 401
        
        data = request.json
        emotion = data.get('emotion')
        intensity = data.get('intensity')
        print(f"Received emotion: {emotion}, intensity: {intensity}")

        if not emotion or not intensity:
            print("Emotion or intensity missing")
            return jsonify({'error': 'Emotion and intensity are required'}), 400

        emotion_key = f"{emotion.upper()}_{intensity.upper()}"
        print(f"Constructed emotion key: {emotion_key}")
        
        if emotion_key not in Emotion.__members__:
            print(f"Invalid emotion key: {emotion_key}")
            return jsonify({'error': 'Invalid emotion or intensity'}), 400

        emotion_enum = Emotion[emotion_key]
        tracks = get_random_tracks(emotion_enum)
        if not tracks:
            print("No tracks found for the given emotion")
            return jsonify({'error': f'No tracks found for emotion: {emotion_key}'}), 404

        # IMPORTANT: Spotify_Playlist_Ids and Top 5 Tracks Ids links
        spotify_playlist_id = create_spotify_playlist(tracks)
        embedded_playlist_code = get_embedded_playlist_code(spotify_playlist_id)
        top_tracks = get_top_recommended_tracks(spotify_playlist_id)
        top_tracks_embedded = [get_embedded_track_code(track.spotify_id) for track in top_tracks]
        
        # Return Output
        return jsonify({
            'embedded_playlist_code': embedded_playlist_code,
            'top_tracks_embedded': top_tracks_embedded
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in create_playlist: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

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
    
    # Error handling
    except Exception as e:
        error_msg = f"Error in recommend_top_tracks: {str(e)}"
        current_app.logger.error(error_msg)
        print(error_msg)
        return jsonify({'error': error_msg}), 500