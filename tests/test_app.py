import pytest, random
from app import create_app
from app.extensions import db
from app.models import Song, Playlist, Emotion

def _populate_test_data():
    emotions = [Emotion.SAD_INTENSE, Emotion.SAD_NORMAL, Emotion.ANGRY_NORMAL, Emotion.ANGRY_INTENSE]
    songs = []

    for i in range(100):
        emotion = random.choice(emotions)
        
        # Adjust audio features based on emotion
        if 'SAD' in emotion.name:
            danceability = random.uniform(0.2, 0.5)
            energy = random.uniform(0.2, 0.5)
            valence = random.uniform(0.1, 0.4)
            tempo = random.uniform(60, 100)
        else:  # ANGRY
            danceability = random.uniform(0.4, 0.7)
            energy = random.uniform(0.7, 1.0)
            valence = random.uniform(0.3, 0.6)
            tempo = random.uniform(100, 160)

        if 'INTENSE' in emotion.name:
            energy = min(1.0, energy + 0.2)
            tempo = min(180, tempo + 20)

        song = Song(
            title=f"Test Song {i+1}",
            artist=f"Test Artist {i+1}",
            album=f"Test Album {(i//5)+1}",
            spotify_id=f"spotify_id_{i+1}",
            emotion=emotion,
            danceability=danceability,
            energy=energy,
            key=random.choice(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']),
            loudness=random.uniform(-15, 0),
            mode=random.choice(['major', 'minor']),
            speechiness=random.uniform(0, 0.5),
            acousticness=random.uniform(0, 1),
            instrumentalness=random.uniform(0, 1),
            liveness=random.uniform(0, 1),
            valence=valence,
            tempo=tempo,
            duration_ms=random.randint(180000, 300000),  # 3-5 minutes
            popularity=random.randint(0, 100)
        )
        songs.append(song)

    db.session.bulk_save_objects(songs)
    db.session.commit()

@pytest.fixture
def client():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def setup_test_data(client):
    with client.application.app_context():
        _populate_test_data()
    yield
    # Cleanup is handled in the `client` fixture

@pytest.fixture
def mock_utils(monkeypatch):
    def mock_get_random_tracks(emotion, min_count=10, max_count=20):
        num_tracks = random.randint(min_count, max_count)
        return [Song(title=f"Test Song {i}", artist=f"Test Artist {i}", spotify_id=f"spotify{i}", 
                     emotion=emotion, popularity=80-i) for i in range(num_tracks)]

    def mock_get_top_recommended_tracks(playlist_id, limit=5):
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return []
        return sorted(playlist.songs, key=lambda x: x.popularity, reverse=True)[:limit]

    monkeypatch.setattr('app.main.get_random_tracks', mock_get_random_tracks)
    monkeypatch.setattr('app.main.get_top_recommended_tracks', mock_get_top_recommended_tracks)

def test_create_playlist(client):
    response = client.post('/api/create_playlist', json={'emotion': 'sad', 'intensity': 'normal'})
    assert response.status_code == 201
    data = response.get_json()
    assert 'playlist_id' in data
    assert 'track_count' in data
    assert 10 <= data['track_count'] <= 20

    # Verify that the playlist was actually created in the database
    with client.application.app_context():
        playlist = Playlist.query.get(data['playlist_id'])
        assert playlist is not None
        assert playlist.emotion == Emotion.SAD_NORMAL
        assert len(playlist.songs) == data['track_count']

def test_recommend_top_tracks(client):
    # First, create a playlist
    create_response = client.post('/api/create_playlist', json={'emotion': 'sad', 'intensity': 'normal'})
    playlist_id = create_response.get_json()['playlist_id']

    # Now get the top recommended tracks
    response = client.get(f'/api/recommend_top_tracks/{playlist_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'top_tracks' in data
    assert len(data['top_tracks']) == 5
    for track in data['top_tracks']:
        assert 'popularity' in track
        assert 'spotify_embed_url' in track
        assert track['spotify_embed_url'].startswith('https://open.spotify.com/embed/track/')

def test_playlist_size_and_top_tracks(client):
    # Create a playlist
    create_response = client.post('/api/create_playlist', json={'emotion': 'sad', 'intensity': 'normal'})
    assert create_response.status_code == 201
    data = create_response.get_json()
    assert 'playlist_id' in data, f"Expected 'playlist_id' in response, got: {data}"
    playlist_id = data['playlist_id']

    # Get the created playlist
    playlist_response = client.get(f'/api/playlist/{playlist_id}')
    assert playlist_response.status_code == 200
    playlist_data = playlist_response.get_json()
    
    # Check if the playlist has 10-20 songs
    assert 10 <= len(playlist_data['tracks']) <= 20

    # Get top recommended tracks
    top_tracks_response = client.get(f'/api/recommend_top_tracks/{playlist_id}')
    assert top_tracks_response.status_code == 200
    top_tracks_data = top_tracks_response.get_json()

    # Check if we have exactly 5 top recommended tracks
    assert len(top_tracks_data['top_tracks']) == 5

    # Check if all top tracks have Spotify embed links
    for track in top_tracks_data['top_tracks']:
        assert 'spotify_embed_url' in track
        assert track['spotify_embed_url'].startswith('https://open.spotify.com/embed/track/')

    # Verify that the top tracks are indeed the most popular ones
    playlist_popularities = [track['popularity'] for track in playlist_data['tracks']]
    top_track_popularities = [track['popularity'] for track in top_tracks_data['top_tracks']]
    assert all(popularity in playlist_popularities for popularity in top_track_popularities)
    assert sorted(top_track_popularities, reverse=True) == top_track_popularities

def test_get_playlist(client):
    # First, create a playlist
    create_response = client.post('/api/create_playlist', json={'emotion': 'sad', 'intensity': 'normal'})
    playlist_id = create_response.get_json()['playlist_id']

    # Now get the playlist
    response = client.get(f'/api/playlist/{playlist_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert 'name' in data
    assert 'emotion' in data
    assert 'tracks' in data
    assert 10 <= len(data['tracks']) <= 20
    for track in data['tracks']:
        assert 'popularity' in track
        assert 'spotify_embed_url' in track
        assert track['spotify_embed_url'].startswith('https://open.spotify.com/embed/track/')

def test_frontend_interaction(client):
    # Simulate frontend interaction
    # 1. Create a playlist
    create_response = client.post('/api/create_playlist', json={'emotion': 'sad', 'intensity': 'normal'})
    assert create_response.status_code == 201, f"Unexpected status code: {create_response.status_code}, response: {create_response.get_json()}"
    create_data = create_response.get_json()
    assert 'playlist_id' in create_data, f"Expected 'playlist_id' in response, got: {create_data}"
    playlist_id = create_data['playlist_id']

    # 2. Get recommended tracks
    recommend_response = client.get(f'/api/recommend_top_tracks/{playlist_id}')
    assert recommend_response.status_code == 200, f"Unexpected status code: {recommend_response.status_code}, response: {recommend_response.get_json()}"
    recommended_tracks = recommend_response.get_json()['top_tracks']
    assert len(recommended_tracks) == 5, f"Expected 5 recommended tracks, got {len(recommended_tracks)}"
    assert all('popularity' in track for track in recommended_tracks)
    assert all('spotify_embed_url' in track for track in recommended_tracks)
    assert all(track['spotify_embed_url'].startswith('https://open.spotify.com/embed/track/') for track in recommended_tracks)

    # 3. Get the created playlist
    playlist_response = client.get(f'/api/playlist/{playlist_id}')
    assert playlist_response.status_code == 200, f"Unexpected status code: {playlist_response.status_code}, response: {playlist_response.get_json()}"
    playlist_data = playlist_response.get_json()
    assert playlist_data['emotion'] == 'SAD_NORMAL', f"Expected emotion 'SAD_NORMAL', got {playlist_data['emotion']}"
    assert 10 <= len(playlist_data['tracks']) <= 20, f"Expected 10-20 tracks, got {len(playlist_data['tracks'])}"
    assert all('popularity' in track for track in playlist_data['tracks'])
    assert all('spotify_embed_url' in track for track in playlist_data['tracks'])
    assert all(track['spotify_embed_url'].startswith('https://open.spotify.com/embed/track/') for track in playlist_data['tracks'])

    print("All frontend interaction tests passed successfully!")