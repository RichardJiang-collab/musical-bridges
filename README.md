# 🎵 Musical Bridges

Welcome to Musical Bridges, a Spotify playlist generator that creates personalized playlists based on emotions and recommends top tracks!

## 📁 Project Structure

```
music_recommendation_system/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── main.py
│   ├── utils.py
│   ├── extensions.py
├── webflow_exporter_base/
│   ├── index.html
│   ├── emotions.html
│   ├── recommendations.html
│   ├── anger-selection.html
│   ├── sadness-selection.html
│   ├── css/
│   │   ├── webflow-style.css
│   ├── js/
│   │   ├── jquery.js
│   │   ├── webflow-script.js
│   ├── images/
│   │   ├── (image files)
├── tests/
│   ├── test_app.py
├── migrations/
│   └── (migration files)
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

## 🚀 Main Functionalities

### Backend

1. **Create Spotify Playlist**: Generates a playlist of 10-20 songs based on emotion and song features.
2. **Top 5 Recommended Songs**: Returns the top 5 most popular songs from the generated playlist as embedded track links.

## 🧠 Algorithm

### Playlist Creation
1. The system selects songs from the database that match the given emotion.
2. It then randomly selects 10-20 tracks from this pool.
3. The selection process considers various song features such as danceability, energy, loudness, speechiness, acousticness, instrumentalness, liveness, valence, tempo, and popularity.

### Top 5 Recommendations
1. From the generated playlist, the system sorts the songs based on their popularity.
2. It then selects the top 5 most popular songs.
3. For each of these songs, it generates a Spotify embedded track link for easy listening.

## 🛠 Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/RichardJiang-collab/musical-bridges.git
   cd musical-bridges
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your .env file with the following variables:
   ```
   SECRET_KEY=your_secret_key
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   FLASK_DEBUG=True  # Set to False in production
   ```

5. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the application:
   ```
   python run.py
   ```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check [issues page](https://github.com/RichardJiang-collab/musical-bridges/issues).

## 📝 License

This project is [MIT](https://choosealicense.com/licenses/mit/) licensed.

## 🎉 Acknowledgements

- Thanks to Spotify for providing the API that makes this project possible.
- Shoutout to all the music lovers who inspire projects like these!

Happy listening! 🎧