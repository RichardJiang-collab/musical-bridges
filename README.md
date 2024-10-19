# 🎵 Musical Bridges

Embark on a musical journey with Musical Bridges, a dynamic Spotify playlist generator that tailors playlists to your emotional state and suggests top tracks to elevate your listening experience.

## 📂 Navigating the Project
Here's a glimpse into the structure of our music recommendation system:

```
music_recommendation_system/
├── app/
│   ├── templates/
│   │   ├── login.html
│   │   ├── profile.html
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

## 🌟 Key Features

1. **Emotion-Driven Playlists**: Craft a playlist of 10-20 songs that resonate with your current mood.
2. **Top Hits Highlight**: Returns the top 5 most popular songs from the generated playlist as embedded track links.


## 🧩 How It Works

### Playlist Generation
1. Our system scours the database for songs that align with your specified emotion.
2. It then handpicks 10-20 tracks from this curated selection.
3. The selection takes into account song attributes like danceability, energy, loudness, and more.

### Top 5 Recommendations
1. The system ranks the songs in your playlist based on their popularity.
2. It selects the top 5 most beloved tracks.
3. For your convenience, it generates Spotify embedded track links for these songs.


## Breaking the Filter Bubble（信息茧房问题）

Musical Bridges is designed to prevent the filter bubble effect, where users might get stuck in a loop of similar music. By intentionally diversifying the genres in our recommendations, we ensure that you're exposed to a rich tapestry of music beyond your initial preferences. This approach aims to broaden your musical horizons and spark excitement in discovering new sounds.

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
