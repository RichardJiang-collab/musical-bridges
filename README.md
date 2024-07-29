# Project Musical Bridges

Musical Bridges is a Flask-based API that recommends music based on user-selected emotions. This README provides an overview of the project, its setup, and how to use the API.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Running the Application](#running-the-application)
8. [API Endpoints](#api-endpoints)
9. [Deployment](#deployment)
10. [Contributing](#contributing)
11. [License](#license)

## Overview

Musical Bridges is a web application that allows users to select an emotion and its intensity, and receive music recommendations based on their selection. The backend is built with Flask and integrates with the Spotify API to fetch playlist data.

## Features

- Emotion selection API
- Music recommendations based on emotions and intensity
- Integration with Spotify API
- SQLite database for storing emotion and playlist data
- CORS support for cross-origin requests

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.7+
- pip (Python package manager)
- Spotify Developer Account (for API credentials)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/musical-bridges.git
   cd musical-bridges
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root directory.
2. Add your Spotify API credentials to the `.env` file:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

## Database Setup

The application uses SQLite as its database. The database will be automatically created when you run the application for the first time. However, you'll need to populate it with initial data for emotions and playlists.

To set up the database manually:

1. Open a Python shell in the project directory:
   ```
   python
   ```

2. Run the following commands:
   ```python
   from app import app, db, Emotion, Playlist
   
   with app.app_context():
       db.create_all()
       
       # Add emotions
       angry = Emotion(name='Angry', intensity='High')
       sad = Emotion(name='Sad', intensity='Low')
       db.session.add_all([angry, sad])
       
       # Add playlists (replace with actual Spotify playlist IDs)
       angry_playlist = Playlist(spotify_id='spotify:playlist:angry_playlist_id', emotion_id=1, intensity='High')
       sad_playlist = Playlist(spotify_id='spotify:playlist:sad_playlist_id', emotion_id=2, intensity='Low')
       db.session.add_all([angry_playlist, sad_playlist])
       
       db.session.commit()
   ```

3. Exit the Python shell:
   ```
   exit()
   ```

## Running the Application

To run the application locally:

```
python app.py
```

The API will be available at `http://localhost:5000`.

## API Endpoints

1. **GET /api/emotions**
   - Retrieves all available emotions.
   - Response: List of emotion objects with `id`, `name`, and `intensity`.

2. **POST /api/select-emotion**
   - Selects an emotion for recommendation.
   - Request body: `{ "emotion_id": 1, "intensity": "High" }`
   - Response: Success message or error if invalid.

3. **GET /api/recommendations**
   - Gets music recommendations based on selected emotion and intensity.
   - Query parameters: `emotion_id` and `intensity`.
   - Response: Spotify playlist ID and top 5 track recommendations.

## Deployment

The application is deployed on Heroku. You can access it at:

https://musical-bridges-063243932240.herokuapp.com/

To deploy your own instance:

1. Create a Heroku account and install the Heroku CLI.
2. Login to Heroku CLI: `heroku login`
3. Create a new Heroku app: `heroku create your-app-name`
4. Push your code to Heroku: `git push heroku main`
5. Set up environment variables on Heroku:
   ```
   heroku config:set SPOTIFY_CLIENT_ID=your_client_id
   heroku config:set SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
