
```
musical-bridges/
│
├── .env                    # Environment variables (not tracked in git)
├── .gitignore              # Git ignore file
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── Procfile                # Heroku deployment file
├── app.py                  # Main application file
```

## Purpose of Each Component

- `.env`: Stores environment variables like API keys and database URLs.
- `.gitignore`: Specifies files and directories that Git should ignore.
- `README.md`: Project overview and setup instructions.
- `requirements.txt`: Lists all Python dependencies for the project.
- `Procfile`: Specifies commands for Heroku deployment.
- `app.py`: The main entry point of the application.

### src/ Directory

- `models.py`: Defines SQLAlchemy models for the database.
- `routes.py`: Contains all the API route definitions.
- `services/`: Houses business logic separated by domain.
  - `emotion_service.py`: Handles emotion-related operations.
  - `spotify_service.py`: Manages Spotify API interactions.
- `utils.py`: Contains utility functions used across the application.
