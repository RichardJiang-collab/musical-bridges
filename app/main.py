from flask import Blueprint, request, jsonify, current_app, redirect, session, url_for, render_template, send_from_directory
from .models import Emotion, User, UserGenre, SavedPlaylistLinks, SavedTopSongsLinks
from .utils import get_random_tracks, get_top_recommended_tracks, create_spotify_playlist, get_embedded_playlist_code, get_embedded_track_code, get_spotify_client
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
from .extensions import db
import time, os, requests

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

SPOTIFY_CLIENT_ID = os.getenv('CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Get Spotify Token
def get_spotify_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token", 
        headers={"Content-Type": "application/x-www-form-urlencoded"}, 
        data={"grant_type": "client_credentials", "client_id": SPOTIFY_CLIENT_ID, "client_secret": SPOTIFY_CLIENT_SECRET}
    )
    return response.json().get("access_token")

# Part 1. Login, Authentication, and Signout
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
    current_app.logger.info(f"Token info set in session: {session['token_info']}")
    access_token = token_info['access_token']
    sp = get_spotify_client(access_token)
    
    try:
        user_profile = sp.current_user()
        display_name = user_profile.get('display_name')
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve user profile: {str(e)}'}), 500
    session['display_name'] = display_name

    user_id = user_profile.get('id')
    if not user_id:
        return jsonify({'error': 'Failed to retrieve Spotify user ID'}), 500
    session['user_id'] = user_id

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        new_user = User(user_id=user_id)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/genres-page')  # First-time login, redirect to genres
    else:
        return redirect('/')  # Existing user, redirect to index

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
    
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.filter_by(user_id=user_id).first()
        
        if user:
            return redirect('/')
        else:
            return redirect('/genres-page')
    
    return render_template('login.html', auth_url=auth_url)

@main.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return redirect('/')


# Part 2. Routes for each page
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

# Part 2.1 Get user's genres
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
    try:
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Part 3. Recommending playlist and top tracks
def get_token():
    token_info = session.get('token_info')
    if not token_info:
        return None
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 1440
    
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

        # Construct emotion key
        emotion_key = f"{emotion.upper()}_{intensity.upper()}"
        print(f"Constructed emotion key: {emotion_key}")
        
        if emotion_key not in Emotion.__members__:
            print(f"Invalid emotion key: {emotion_key}")
            return jsonify({'error': 'Invalid emotion or intensity'}), 400

        # Get random tracks based on emotion
        emotion_enum = Emotion[emotion_key]
        tracks = get_random_tracks(emotion_enum)
        if not tracks:
            print("No tracks found for the given emotion")
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

# Part 4. Retrieve links and resources for starred playlists and songs
@main.route('/api/save_playlist', methods=['POST'])
def save_playlist():    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Failed to retrieve Spotify user ID'}), 500
    session['user_id'] = user_id

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        new_user = User(user_id=user_id)
        db.session.add(new_user)
        db.session.commit()

    data = request.get_json()
    new_playlist = SavedPlaylistLinks(user_id=user_id, playlist_link=data['link'])
    db.session.add(new_playlist)
    db.session.commit()
    return jsonify({'message': 'Playlist saved successfully!'}), 201

@main.route('/api/save_top_song', methods=['POST'])
def save_top_song():
    user_id = session.get('user_id')
    song_link = request.json.get('link').strip()  # Ensure the input is stripped of leading/trailing whitespace

    if not user_id:
        return jsonify({'error': 'Failed to retrieve Spotify user ID'}), 500

    # Extract only the track ID, removing any unexpected HTML tags
    try:
        # Check if the input link contains an iframe tag and isolate the src if it does
        if "<iframe" in song_link:
            # Extract the URL from within the iframe tag
            start = song_link.find("src=\"") + 5
            end = song_link.find("\"", start)
            song_link = song_link[start:end]

        # Further split to get the track ID
        track_id = song_link.split("/track/")[-1].split("?")[0]
    except IndexError:
        return jsonify({'error': 'Invalid song link format'}), 400

    # Generate the correctly formatted embed URL
    embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator"

    # Save only the clean embed URL to the database
    new_song = SavedTopSongsLinks(user_id=user_id, top_songs_links=embed_url)
    db.session.add(new_song)
    db.session.commit()

    return jsonify({'message': 'Song saved successfully!'}), 201

@main.route('/api/get_saved_playlists', methods=['GET'])
def get_saved_playlists():
    playlists = SavedPlaylistLinks.query.all()
    playlist_data = [
        {"playlist_link": p.playlist_link} for p in playlists
    ]
    return jsonify(playlist_data), 200

@main.route('/api/get_saved_tracks', methods=['GET'])
def get_saved_tracks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    tracks = SavedTopSongsLinks.query.filter_by(user_id=user_id).all()
    track_data = [{"track_link": t.top_songs_links} for t in tracks]
    return jsonify(track_data), 200

@main.route('/api/playlist_info', methods=['GET'])
def get_playlist_info():
    playlist_link = request.args.get('link')  # Get the link from query param
    playlist_id = playlist_link.split("/")[-1].split("?")[0]  # Extract ID from URL
    token = get_spotify_token()

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200:
        return jsonify({
            "name": data["name"],
            "image_url": data["images"][0]["url"]
        }), 200
    else:
        return jsonify({"error": "Unable to fetch playlist data"}), 400

# # Simulate a User Login and Set user_id
# @main.route('/test_login', methods=['GET'])
# def test_login():
#     # Set user_id manually for testing purposes
#     session['user_id'] = 'test_user_id'
#     session.permanent = True  # This should respect PERMANENT_SESSION_LIFETIME in config
#     return jsonify({'message': 'Test login successful. User ID set in session.'}), 200
