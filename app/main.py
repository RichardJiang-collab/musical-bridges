from flask import Blueprint, request, jsonify, current_app, redirect, session, url_for, render_template, send_from_directory
from .models import Emotion, User, UserGenre
from .utils import get_random_tracks, get_top_recommended_tracks, create_spotify_playlist, get_embedded_playlist_code, get_embedded_track_code, get_spotify_client
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
import time
from .extensions import db

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

@main.route('/callback')
@main.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
        scope="playlist-modify-private",
        cache_handler=None
    )
    
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Authorization code not found'}), 400

    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve access token: {str(e)}'}), 500

    session['token_info'] = token_info

    # Use the access token to get the user's profile from Spotify
    access_token = token_info['access_token']
    
    # Make an authenticated request to Spotify API to get the user profile
    sp = get_spotify_client(access_token)  # Assuming get_spotify_client is defined elsewhere to get a Spotipy client
    try:
        user_profile = sp.current_user()
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve user profile: {str(e)}'}), 500

    # Extract the Spotify user ID from the profile
    user_id = user_profile.get('id')
    if not user_id:
        return jsonify({'error': 'Failed to retrieve Spotify user ID'}), 500

    session['user_id'] = user_id

    # Check if the user already exists in the database
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        new_user = User(user_id=user_id)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('main.genres_page'))  # First-time login, redirect to genres
    else:
        return redirect(url_for('main.index'))  # Existing user, redirect to index

def check_auth():
    if 'token_info' not in session:
        return redirect(url_for('main.login'))
    return None

@main.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
        scope="playlist-modify-private"
    )
    auth_url = sp_oauth.get_authorize_url()
    
    # After successful Spotify login
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.filter_by(user_id=user_id).first()
        
        if user:
            return redirect(url_for('main.index'))
        else:
            return redirect(url_for('main.genres-page'))
    
    return render_template('login.html', auth_url=auth_url)

@main.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(current_app.static_folder, filename)

@main.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return redirect(url_for('main.index')), 200

@main.route('/')
def index():
    return send_from_directory(current_app.static_folder, 'index.html')

@main.route('/emotions')
def emotions():
    auth_check = check_auth()
    if auth_check:
        return auth_check
    return send_from_directory(current_app.static_folder, 'emotions.html')

@main.route('/anger-selection')
def anger_selection():
    auth_check = check_auth()
    if auth_check:
        return auth_check
    return send_from_directory(current_app.static_folder, 'anger-selection.html')

@main.route('/sadness-selection')
def sadness_selection():
    auth_check = check_auth()
    if auth_check:
        return auth_check
    return send_from_directory(current_app.static_folder, 'sadness-selection.html')

@main.route('/recommendations')
def recommendations():
    auth_check = check_auth()
    if auth_check:
        return auth_check
    return send_from_directory(current_app.static_folder, 'recommendations.html')

@main.route('/user-profile')
def user_profile():
    auth_check = check_auth()
    if auth_check:
        return auth_check
    return send_from_directory(current_app.static_folder, 'profile.html')

@main.route('/genres-page', methods=['GET'])
def genres_page():
    auth_check = check_auth()
    if auth_check:
        return auth_check
    
    return send_from_directory(current_app.static_folder, 'genre.html')

@main.route('/genres', methods=['GET'])
def get_user_genres():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403

    genres = UserGenre.query.filter_by(user_id=user_id).all()
    genre_list = [genre.genre for genre in genres]
    
    return jsonify({'genres': genre_list})

@main.route('/update-genres', methods=['POST'])
def update_genres():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403
    
    data = request.get_json()
    selected_genres = data.get('genres', [])

    # Delete old genres for the user
    UserGenre.query.filter_by(user_id=user_id).delete()

    # Add new genres
    for genre in selected_genres:
        new_genre = UserGenre(user_id=user_id, genre=genre)
        db.session.add(new_genre)
    
    db.session.commit()
    return jsonify({'success': True})

def get_token():
    token_info = session.get('token_info')
    if not token_info:
        return None
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    
    if is_expired:
        sp_oauth = SpotifyOAuth(
            client_id=current_app.config['SPOTIFY_CLIENT_ID'],
            client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
            redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
            scope="playlist-modify-private",
            cache_handler=None
        )
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info['access_token']

@main.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    access_token = get_token()
    if not access_token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    sp = get_spotify_client(access_token)
    
    try:
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

        spotify_playlist_id = create_spotify_playlist(tracks)
        embedded_playlist_code = get_embedded_playlist_code(spotify_playlist_id)
        top_tracks = get_top_recommended_tracks(spotify_playlist_id)
        top_tracks_embedded = [get_embedded_track_code(track.spotify_id) for track in top_tracks]
        
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
    
    except Exception as e:
        error_msg = f"Error in recommend_top_tracks: {str(e)}"
        current_app.logger.error(error_msg)
        print(error_msg)
        return jsonify({'error': error_msg}), 500