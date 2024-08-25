from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from .extensions import db
from .models import Playlist, Emotion
from .utils import get_random_tracks, get_top_recommended_tracks

main = Blueprint('main', __name__)


@main.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    data = request.json
    emotion = data.get('emotion')
    intensity = data.get('intensity')

    if not emotion or not intensity:
        return jsonify({'error': 'Emotion and intensity are required'}), 400

    try:
        emotion_enum = Emotion[f"{emotion.upper()}_{intensity.upper()}"]
        playlist = Playlist(name=f"{emotion.capitalize()} ({intensity.capitalize()}) Playlist", emotion=emotion_enum)
        
        tracks = get_random_tracks(emotion_enum)
        if not tracks:
            return jsonify({'error': 'No tracks found for the given emotion'}), 404
        
        playlist.songs.extend(tracks)
        
        db.session.add(playlist)
        db.session.commit()
        
        return jsonify({
            'message': 'Playlist created successfully', 
            'playlist_id': playlist.id,
            'track_count': len(tracks)
        }), 201
    except KeyError as e:
        current_app.logger.error(f"KeyError in create_playlist: {str(e)}")
        return jsonify({'error': f'Invalid emotion or intensity: {str(e)}'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"SQLAlchemyError in create_playlist: {str(e)}")
        return jsonify({'error': f'Database error occurred: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in create_playlist: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@main.route('/api/recommend_top_tracks/<int:playlist_id>', methods=['GET'])
def recommend_top_tracks(playlist_id):
    try:
        top_tracks = get_top_recommended_tracks(playlist_id)
        
        tracks_data = [{
            'id': track.id,
            'title': track.title,
            'artist': track.artist,
            'album': track.album,
            'popularity': track.popularity,
            'spotify_embed_url': f"https://open.spotify.com/embed/track/{track.spotify_id}"
        } for track in top_tracks]
        
        return jsonify({'top_tracks': tracks_data}), 200
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred'}), 500

@main.route('/api/playlist/<int:playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    try:
        playlist = db.session.get(Playlist, playlist_id)
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404

        tracks_data = [{
            'id': song.id,
            'title': song.title,
            'artist': song.artist,
            'album': song.album,
            'popularity': song.popularity,
            'spotify_embed_url': f"https://open.spotify.com/embed/track/{song.spotify_id}"
        } for song in playlist.songs]

        return jsonify({
            'id': playlist.id,
            'name': playlist.name,
            'emotion': playlist.emotion.value,
            'tracks': tracks_data
        }), 200
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred'}), 500