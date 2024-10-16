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
│   ├── genre.html
│   ├── profile.html
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

## Addressing Filter Bubble Problem （信息茧房问题）

In a music system with a filter bubble problem, users may be stuck in a narrow range of musical styles and genres. For example, if you initially listen to pop music, the system may continuously recommend similar pop tunes, preventing you from discovering other rich musical forms such as classical, jazz, or world music. This limits your musical exploration and reduces the excitement and surprise that comes from encountering new sounds. 

To properly address this problem, we implemented an algorithm to enhance our recommendation system by incorporating a diverse range of genres into our final suggestions. This approach not only caters to users' personalized preferences but also introduces them to a broader spectrum of genres they might not have been aware of or interested in previously. By doing so, we aim to expand their horizons and enrich their experience with a more eclectic selection of content.

## 🛠 Usage Instructions
Go to the current Musical Bridges official website https://musical-bridges-063243932240.herokuapp.com/ to check out!

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check [issues page](https://github.com/RichardJiang-collab/musical-bridges/issues).

## 📝 License

This project is [MIT](https://choosealicense.com/licenses/mit/) licensed.

## 🎉 Acknowledgements

- Thanks to Spotify for providing the API that makes this project possible.
- Shoutout to all the music lovers who inspire projects like these!

Happy listening! 🎧
