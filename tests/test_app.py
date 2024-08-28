import pytest
from app import create_app, db
from app.models import Song, Emotion
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def mock_spotify_api():
    with patch('app.utils.get_spotify_client') as mock_get_client:
        mock_spotify = MagicMock()
        mock_spotify.me.return_value = {'id': 'test_user_id'}
        mock_spotify.user_playlist_create.return_value = {'id': 'test_playlist_id'}
        mock_get_client.return_value = mock_spotify

        with patch('app.utils.create_spotify_playlist') as mock_create_playlist:
            mock_create_playlist.return_value = 'test_playlist_id'

        with patch('app.utils.get_embedded_playlist_code') as mock_playlist_code:
            mock_playlist_code.return_value = '<iframe style="border-radius:12px" src="https://open.spotify.com/embed/playlist/test_playlist_id?utm_source=generator" width="100%" height="352" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'

        with patch('app.utils.get_embedded_track_code') as mock_track_code:
            mock_track_code.side_effect = lambda track_id: f'<iframe style="border-radius:12px" src="https://open.spotify.com/embed/track/{track_id}?utm_source=generator" width="100%" height="352" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'

        yield mock_spotify

def create_test_songs():
    songs = [
        Song(title=f"Test Song {i}", artist=f"Test Artist {i}", spotify_id=f"test_id_{i}",
             emotion=Emotion.SAD_NORMAL, danceability=0.5, energy=0.5, key="C",
             loudness=-10, mode="major", speechiness=0.1, acousticness=0.2,
             instrumentalness=0.3, liveness=0.4, valence=0.6, tempo=120,
             duration_ms=200000, popularity=50)
        for i in range(1, 21)
    ]
    db.session.add_all(songs)
    db.session.commit()

def test_create_playlist(client, mock_spotify_api):
    create_test_songs()
    
    response = client.post('/api/create_playlist', json={
        'emotion': 'sad',
        'intensity': 'normal'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'playlist_id' in data
    assert 'spotify_playlist_id' in data
    assert 'embedded_playlist_code' in data
    assert data['track_count'] >= 10 and data['track_count'] <= 20

    print("\n--- Embedded Playlist Code ---")
    print(data['embedded_playlist_code'])

def test_recommend_top_tracks(client, mock_spotify_api):
    create_test_songs()
    
    # Create a playlist first
    response = client.post('/api/create_playlist', json={
        'emotion': 'sad',
        'intensity': 'normal'
    })
    playlist_id = response.get_json()['playlist_id']
    
    # Now get top recommended tracks
    response = client.get(f'/api/recommend_top_tracks/{playlist_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'top_tracks' in data
    assert len(data['top_tracks']) == 5
    
    print("\n--- Top 5 Recommended Tracks Embedded Codes ---")
    for i, track in enumerate(data['top_tracks'], 1):
        assert 'embedded_track_code' in track
        print(f"\n{i}. {track.get('title', 'Unknown Title')} - {track.get('artist', 'Unknown Artist')}:")
        print(track['embedded_track_code'])

def test_get_playlist(client, mock_spotify_api):
    create_test_songs()
    
    # Create a playlist first
    response = client.post('/api/create_playlist', json={
        'emotion': 'sad',
        'intensity': 'normal'
    })
    playlist_id = response.get_json()['playlist_id']
    
    # Now get the playlist
    response = client.get(f'/api/playlist/{playlist_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert 'name' in data
    assert 'emotion' in data
    assert 'tracks' in data
    
    print("\n--- Playlist Tracks Embedded Codes ---")
    for i, track in enumerate(data['tracks'], 1):
        assert 'embedded_track_code' in track
        print(f"\n{i}. {track.get('title', 'Unknown Title')} - {track.get('artist', 'Unknown Artist')}:")
        print(track['embedded_track_code'])

# ... (other test functions remain the same)

def test_create_playlist_invalid_emotion(client):
    response = client.post('/api/create_playlist', json={
        'emotion': 'invalid',
        'intensity': 'normal'
    })
    
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_recommend_top_tracks_invalid_playlist(client):
    response = client.get('/api/recommend_top_tracks/999')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'top_tracks' in data
    assert len(data['top_tracks']) == 0

def test_get_playlist_invalid_id(client):
    response = client.get('/api/playlist/999')
    
    assert response.status_code == 404
    assert 'error' in response.get_json()