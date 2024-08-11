# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Heroku: https://musical-bridges-063243932240.herokuapp.com/

# Load environment variables
load_dotenv()

app = Flask(__name__)
# CORS(app)  # Enable CORS for all domains on all routes
cors = CORS(app, resources={r"/*": {"origins": "http://localhost:5000"}})
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///musical_bridges.db'
db = SQLAlchemy(app)

# Spotify API setup
client_credentials_manager = SpotifyClientCredentials(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
)

sp = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)


print("running app.py")

# Add a root route
@app.route('/')
@cross_origin()
def home():
    return "Welcome to Musical Bridges API!"

# Database models
class Emotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.String(20), nullable=False)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(100), nullable=False)
    emotion_id = db.Column(db.Integer, db.ForeignKey('emotion.id'), nullable=False)
    intensity = db.Column(db.String(20), nullable=False)


# API routes
@app.route('/api/emotions', methods=['GET'])
@cross_origin()
def get_emotions():
    emotions = Emotion.query.all()
    print("in get_emotions")
    return jsonify([{'id': e.id, 'name': e.name, 'intensity': e.intensity} for e in emotions])


@app.route('/api/recommendations', methods=['GET'])
@cross_origin()
def get_recommendations():
    print("starting in get_recommendations")
    emotion = request.args.get('emotion')
    intensity = request.args.get('intensity')

   
    # emotion_id = request.args.get('emotion_id')
    # intensity = request.args.get('intensity')

    # emotion = Emotion.query.get(emotion_id)
    if not emotion:
        return jsonify({'error': 'Invalid emotion'}), 400

    # Define seed tracks and audio features for each emotion and intensity
    emotion_seeds = {
        'angry': {
            'normal': {
                'tracks': ['spotify:track:7lQ8MOhq6NdnduCmKxChargebyViolentsplg', 'spotify:track:3YuaBvuZqcwN3CEAyyoaei'],
                'target_energy': 0.8,
                'target_valence': 0.3,
                'min_tempo': 120,
            },
            'intense': {
                'tracks': ['spotify:track:7LoYxCkYqHK1kPnDtV51Bm', 'spotify:track:5Hqs4TwIBt3IwB29yg8C0h'],
                'target_energy': 0.9,
                'target_valence': 0.2,
                'min_tempo': 140,
            }
        },
        'sadness': {
            'normal': {
                'tracks': ['spotify:track:6b2RcmUt1g9N9mQ3CbjX2Y', 'spotify:track:3JOVTQ5h8HGFnDdp4VT3MP'],
                'target_energy': 0.4,
                'target_valence': 0.3,
                'max_tempo': 100,
            },
            'intense': {
                'tracks': ['spotify:track:4RCWB3V8V0dignt99LZ8vH', 'spotify:track:1BxfuPKGuaTgP7aM0Bbdwr'],
                'target_energy': 0.3,
                'target_valence': 0.2,
                'max_tempo': 80,
            }
        }
    }

    # Get the appropriate seed tracks and audio features
    # emotion_name = emotion.name.lower()
    emotion_name = emotion
    if emotion_name not in emotion_seeds or intensity not in emotion_seeds[emotion_name]:
        return jsonify({'error': 'Unsupported emotion or intensity'}), 400

    seed_data = emotion_seeds[emotion_name][intensity]

    # Get recommendations from Spotify API
    recommendations = sp.recommendations(
        seed_tracks=seed_data['tracks'],
        target_energy=seed_data['target_energy'],
        target_valence=seed_data['target_valence'],
        min_tempo=seed_data.get('min_tempo'),
        max_tempo=seed_data.get('max_tempo'),
        limit=5
    )

    # Format the recommendations
    formatted_recommendations = [
        {'name': track['name'], 'artist': track['artists'][0]['name'], 'id': track['id']}
        for track in recommendations['tracks']
    ]
    #dummy line


    return jsonify({
        'emotion': emotion_name,
        'intensity': intensity,
        'recommendations': formatted_recommendations
    })

@app.route('/api/select-emotion', methods=['POST'])
@cross_origin()
def select_emotion():
    data = request.json
    emotion_id = data.get('emotion_id')
    intensity = data.get('intensity')

    emotion = Emotion.query.get(emotion_id)
    if not emotion or emotion.intensity != intensity:
        return jsonify({'error': 'Invalid emotion or intensity'}), 400
    # print("in select_emotion")
    return jsonify({'message': 'Emotion selected successfully'})





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)