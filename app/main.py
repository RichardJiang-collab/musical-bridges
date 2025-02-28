from flask import Blueprint, request, jsonify, current_app, redirect, session, url_for, render_template, send_from_directory
from .utils import get_random_tracks, get_top_recommended_tracks, create_spotify_playlist, get_embedded_playlist_code, get_embedded_track_code, get_spotify_client
from .models import Emotion, User, UserGenre, SavedTopSongsLinks
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
from .extensions import db
import time, httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
emotion_map = {
    "Joy": (0.8, 0.8),
    "Love": (0.9, 0.7),
    "Devotion": (0.8, -0.2),
    "Tender feelings": (0.8, -0.2),
    "Suffering": (-0.8, -0.5),
    "Weeping": (-0.7, -0.5),
    "High spirits": (0.8, 0.9),
    "Low spirits": (-0.7, -0.4),
    "Anxiety": (-0.6, 0.8),
    "Grief": (-0.8, -0.6),
    "Dejection": (-0.7, -0.5),
    "Despair": (-0.9, -0.7),
    "Anger": (-0.8, 0.8),
    "Hatred": (-0.9, 0.7),
    "Disdain": (-0.7, 0.7),
    "Contempt": (-0.7, 0.8),
    "Disgust": (-0.8, 0.6),
    "Guilt": (-0.6, -0.5),
    "Pride": (0.7, 0.6),
    "Helplessness": (-0.8, -0.5),
    "Patience": (0.7, -0.3),
    "Affirmation": (0.7, -0.2),
    "Negation": (0.0, 0.0),  # Ambiguous; set as neutral
    "Surprise": (0.8, 0.8),
    "Fear": (-0.8, 0.8),
    "Self-attention": (0.5, -0.3),
    "Shyness": (-0.2, -0.3),
    "Modesty": (0.3, -0.2),
    "Blushing": (-0.1, 0.2),
    "Reflection": (0.6, -0.3),
    "Mediation": (0.8, -0.4),  # Assuming "Mediation" means "Meditation"
    "Ill-temper": (-0.7, 0.9),
    "Sulkiness": (-0.6, 0.8),
    "Determination": (0.7, 0.8)
}

main = Blueprint('main', __name__)
CORS(main, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

def init_api_client():
    global client
    http_client = httpx.Client(proxies=None)
    client = OpenAI(
        api_key=current_app.config['MOONSHOT_API_KEY'],
        base_url="https://api.moonshot.cn/v1",
        http_client=http_client
    )

#* DEBUGGING
@main.route('/debug-env')
def debug_env():
    return jsonify({
        'SPOTIFY_SCOPES': current_app.config.get('SPOTIFY_SCOPES'),
        'OTHER_VARIABLE': current_app.config.get('OTHER_VARIABLE')
    })

#* Part 1. Login, Authentication, Get Token, Signout
@main.route('/callback')
def callback():
    # Initialize Spotify OAuth
    sp_oauth = SpotifyOAuth(
        client_id=current_app.config['SPOTIFY_CLIENT_ID'],
        client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
        scope=current_app.config['SPOTIFY_SCOPES'],
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

def get_token():
    token_info = session.get('token_info')
    if not token_info:
        return None
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 1440
    
    if is_expired:
        sp_oauth = SpotifyOAuth(
            client_id=current_app.config('SPOTIFY_CLIENT_ID'),
            client_secret=current_app.config('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=current_app.config('SPOTIFY_REDIRECT_URI'),
            scope=current_app.config('SPOTIFY_SCOPES'),
            cache_handler=None
        )
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info['access_token']

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


#* Route for understanding and pinpointing the user's emotion
@main.route('/api/refineEmotion', methods=['POST'])
def refine_emotion():
    try:
        data = request.get_json()
        main_emotion, emotion_detail = data.get('mainEmotion'), data.get('emotionDetail')
        if not main_emotion:
            return jsonify({'error': 'Main emotion is required'}), 400
        if emotion_detail and emotion_detail.strip():
            prompt = f"""请根据以下描述细化情感，并在以下情感列表中选择最匹配的情感，仅回复情感名称：
                情感描述: "{emotion_detail}"
                主要情感: "{main_emotion}"
                情感列表: Joy, Love, Devotion, Tender feelings, Suffering, Weeping, High spirits, Low spirits, Anxiety, Grief, Dejection, Despair, Anger, Hatred, Disdain, Contempt, Disgust, Guilt, Pride, Helplessness, Patience, Affirmation, Negation, Surprise, Fear, Self-attention, Shyness, Modesty, Blushing, Reflection, Meditation, Ill-temper, Sulkiness, Determination.
            """
            completion = client.chat.completions.create(
                model = "moonshot-v1-8k",
                messages = [
                    {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
                    {"role": "user", "content": prompt}
                ],
                temperature = 0.3,
                max_tokens=20
            )
            refine_emotion = completion.choices[0].message.content
            return jsonify({'refinedEmotion': refine_emotion})
        else:
            return jsonify({'emotion': main_emotion})
    except Exception as error:
        print(f"Error refining emotion: {error}")
        return jsonify({'error': 'Failed to refine emotion'}), 500


"""
TODO: Update the API + recommendations.html (for using the API) for recommendation 
(from using solely based on the specific emotion and the values corresponding to the emotion)
"""

#* Part 3. Functions for creating tailored playlist
def classify_emotion(emotion):
    valence, arousal = emotion_map.get(emotion, (0, 0))
    if valence >= 0.67 and arousal >= 0.67:
        return "JOY"  # High Valence, High Arousal
    elif valence >= 0.67 and arousal < 0.67:
        return "TENDER"  # High Valence, Low Arousal
    elif valence < 0.67 and arousal >= 0.67:
        return "ANGER"  # Low Valence, High Arousal
    else:
        return "SADNESS"  # Low Valence, Low Arousal

@main.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    auth_check = check_auth()
    if auth_check:
        return auth_check  # Redirect to login if not authenticated

    # Get Access Token for Spotify Access
    current_app.logger.info("create_playlist called")
    access_token = get_token()
    current_app.logger.info(f"Access token: {access_token}")

    if not access_token:
        current_app.logger.warning("No access token found")
        return redirect(url_for('main.login'))
        
    
    # Get Spotify client
    sp = get_spotify_client(access_token)
    if not sp:
        raise Exception("Spotify client not authenticated")
    
    try:
        # 1. Retrieve emotion from request
        data = request.json
        emotion = data.get('emotion')
        emotion = emotion.capitalize()
        current_app.logger.info(f'Received emotion: {emotion}')

        # 2. Classify emotion + Debug
        emotion_key = classify_emotion(emotion)
        if emotion_key not in Emotion.__members__:
            print(f"Invalid emotion key: {emotion_key}")
            return jsonify({'error': 'Invalid emotion'}), 400

        # 3. Get random tracks based on emotion
        emotion_enum = Emotion[emotion_key]
        tracks = get_random_tracks(emotion_enum)
        if not tracks:
            return jsonify({'error': f'No tracks found for emotion: {emotion_key}'}), 404

        # 4. Create Spotify playlist
        spotify_playlist_id = create_spotify_playlist(tracks)
        if not spotify_playlist_id:
            return jsonify({'error': 'Failed to create Spotify playlist'}), 500
        
        # 5. Get embedded playlist code
        embedded_playlist_code = get_embedded_playlist_code(spotify_playlist_id)
        current_app.logger.info(f"Embedded playlist code: {embedded_playlist_code}")
        
        # 6. Get top recommended tracks
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

# TODO: Ends here


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
