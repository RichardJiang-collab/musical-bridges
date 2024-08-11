# 🎶 Project Musical Bridges 🌁

Musical Bridges is a Flask-based API that recommends music based on user-selected emotions. This README provides an overview of the project, its setup, and how to use the API.

## 🌴 Overview

Musical Bridges is a web application that allows users to select an emotion and its intensity, and receive music recommendations based on their selection. The backend is built with Flask and integrates with the Spotify API to fetch playlist data.

## 🛠️ Features

- Emotion selection API
- Music recommendations based on emotions and intensity
- Integration with Spotify API
- SQLite database for storing emotion and playlist data
- CORS support for cross-origin requests

## 🚀 Setup and Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Spotify Developer account for API access

### Environment Setup

1. Clone the repository:
   ```
   git clone https://github.com/RichardJiang-collab/musical-bridges.git
   cd musical-bridges
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r app/requirements.txt
   ```

### API Keys

1. Create a Spotify Developer account at https://developer.spotify.com/
2. Create a new application to obtain your Client ID and Client Secret
3. Create a `.env` file in the project root and add your Spotify credentials:
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

## 🏃‍♂️ Running the Backend

1. Ensure your virtual environment is activated
2. Run the Flask application:
   ```
   python app.py
   ```
3. The server will start, and you should see output indicating it's running on `http://127.0.0.1:5000/`

## 🔗 API Endpoints

- `GET /api/emotions`: Get all available emotions
- `POST /api/select-emotion`: Select an emotion and intensity
- `GET /api/recommendations`: Get music recommendations based on selected emotion and intensity

## 🧪 Testing

(Add information about running tests once you have implemented them)

## 🤝 Contributing

(Add guidelines for contributing to the project)

## 📄 License

(Add license information for your project)
