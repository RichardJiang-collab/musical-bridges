from flask import Blueprint, request, jsonify, current_app, redirect, session, url_for, render_template, send_from_directory
from .utils import get_random_tracks, get_top_recommended_tracks, create_spotify_playlist, get_embedded_playlist_code, get_embedded_track_code, get_spotify_client
from .models import Emotion, User, UserGenre, SavedPlaylistLinks, SavedTopSongsLinks
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
from .extensions import db
import os
import time
from dotenv import load_dotenv

load_dotenv()

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

#* Part 1. Login, Authentication, and Signout
@main.route('/callback')
def callback():
    # Initialize Spotify OAuth
    sp_oauth = SpotifyOAuth(
        client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
        client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.environ.get('SPOTIFY_REDIRECT_URI'),
        scope=os.environ.get('SPOTIFY_SCOPES'),
        cache_handler=None
    )
    
    # Retrieve authorization code from the request
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Authorization code not found'}), 400
    
    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        session['token_info'] = token_info
        current_app.logger.info("Token retrieved and stored in session.")
    except Exception as e:
        current_app.logger.error(f"Failed to retrieve access token: {e}")
        return jsonify({'error': f'Failed to retrieve access token: {str(e)}'}), 500

    access_token = token_info.get('access_token')
    if not access_token:
        return jsonify({'error': 'Access token not found in token info'}), 500

    sp = get_spotify_client(access_token)
    try:
        user_profile = sp.current_user()
        display_name = user_profile.get('display_name', 'Unknown User')
        user_id = user_profile.get('id')
        if not user_id:
            raise ValueError('Failed to retrieve Spotify user ID')
    except Exception as e:
        current_app.logger.error(f"Failed to retrieve user profile: {e}")
        return jsonify({'error': f'Failed to retrieve user profile: {str(e)}'}), 500

    # Store user details in session
    session['display_name'] = display_name
    session['user_id'] = user_id
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        return redirect('/emotions')  # Existing user, redirect to emotions
    else:
        new_user = User(user_id=user_id, display_name=display_name)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/genres-page')

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
        scope=current_app.config['SPOTIFY_SCOPES'],
        cache_handler=None
    )
    auth_url = sp_oauth.get_authorize_url()
    
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.filter_by(user_id=user_id).first()
        
        if user:
            return redirect('/emotions')
        else:
            return redirect('/genres-page')
    
    return render_template('login.html', auth_url=auth_url)

@main.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return redirect('/')

#* Part 2. Routes for each page of the website
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
    display_name = session.get('display_name', 'User')
    return render_template('profile.html', display_name=display_name)

@main.route('/genres-page', methods=['GET'])
def genres_page():
    auth_check = check_auth()
    if auth_check:
        return auth_check
    return send_from_directory(current_app.static_folder, 'genre.html')

#* Part 3. Functions for creating tailored playlist
def get_token():
    token_info = session.get('token_info')
    if not token_info:
        return None
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 1440
    
    if is_expired:
        sp_oauth = SpotifyOAuth(
            client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
            client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.environ.get('SPOTIFY_REDIRECT_URI'),
            scope=os.environ.get('SPOTIFY_SCOPES'),
            cache_handler=None
        )
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info['access_token']

@main.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    current_app.logger.info("create_playlist called")
    access_token = get_token()
    current_app.logger.info(f"Access token: {access_token}")
    if not access_token:
        current_app.logger.warning("No access token found")
        return jsonify({'error': 'Not authenticated'}), 401
    
    sp = get_spotify_client(access_token)
    
    try:
        data = request.json
        emotion = data.get('emotion')
        intensity = data.get('intensity')
        current_app.logger.info(f'Received emotion: {emotion}, intensity: {intensity}')

        emotion_key = f"{emotion.upper()}_{intensity.upper()}"  # Construct emotion key
        if emotion_key not in Emotion.__members__:
            print(f"Invalid emotion key: {emotion_key}")
            return jsonify({'error': 'Invalid emotion or intensity'}), 400

        # Get random tracks based on emotion
        emotion_enum = Emotion[emotion_key]
        tracks = get_random_tracks(emotion_enum)
        if not tracks:
            return jsonify({'error': f'No tracks found for emotion: {emotion_key}'}), 404

        # Create Spotify playlist
        spotify_playlist_id = create_spotify_playlist(tracks)
        if not spotify_playlist_id:
            return jsonify({'error': 'Failed to create Spotify playlist'}), 500
        
        # Get embedded playlist code
        embedded_playlist_code = get_embedded_playlist_code(spotify_playlist_id)
        top_tracks = get_top_recommended_tracks(spotify_playlist_id)
        if not top_tracks:
            top_tracks = []
        
        top_tracks_embedded = [get_embedded_track_code(track.spotify_id) for track in top_tracks]
        return jsonify({
            'embedded_playlist_code': embedded_playlist_code,
            'top_tracks_embedded': top_tracks_embedded
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in create_playlist: {str(e)}")
        return jsonify({'error': str(e)}), 500

#* Part 4. Function for recommending tailored top 5 tracks to the users
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

#* Part 5. Retrieve and Update user's choosen genres
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
    UserGenre.query.filter_by(user_id=user_id).delete()  # Delete old genres for the user

    # Add new genres
    for genre in selected_genres:
        new_genre = UserGenre(user_id=user_id, genre=genre)
        db.session.add(new_genre)
    
    db.session.commit()
    try:
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#* Part 6. Allowing users to save tracks they love
@main.route('/api/save_top_song', methods=['POST'])
def save_top_song():
    user_id = session.get('user_id')
    song_link = request.json.get('link').strip()  # Ensure the input is stripped of leading/trailing whitespace
    if not user_id:
        return jsonify({'error': 'Failed to retrieve Spotify user ID'}), 500

    try:
        if "<iframe" in song_link:
            start = song_link.find("src=\"") + 5
            end = song_link.find("\"", start)
            song_link = song_link[start:end]
        track_id = song_link.split("/track/")[-1].split("?")[0]   # Further split to get the track ID
    except IndexError:
        return jsonify({'error': 'Invalid song link format'}), 400

    embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator"  # Generate the correctly formatted embed URL
    new_song = SavedTopSongsLinks(user_id=user_id, top_songs_links=embed_url)
    db.session.add(new_song)
    db.session.commit()

    return jsonify({'message': 'Song saved successfully!'}), 201

@main.route('/api/get_saved_tracks', methods=['GET'])
def get_saved_tracks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    tracks = SavedTopSongsLinks.query.filter_by(user_id=user_id).all()
    track_data = [{"track_link": t.top_songs_links} for t in tracks]
    return jsonify(track_data), 200
