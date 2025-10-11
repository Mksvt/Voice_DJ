# Voice DJ — Voice-Activated Music Assistant

Voice DJ is a lightweight Python voice assistant that recognizes a wake word and plays music on your Spotify account. It uses Vosk for offline wake-word/command detection and OpenAI Whisper (via OpenAI API) for speech-to-text, and Spotipy to control Spotify playback.

Key features

- Wake-word detection using Vosk (offline)
- Short voice command recording and transcription using OpenAI Whisper
- Searches and plays the top Spotify track matching the transcribed command
- Simple, single-file implementation (main.py) for easy experimentation

Project name and purpose

Voice DJ — convenience tool to control Spotify playback with voice commands in Russian (configurable) while keeping wake-word detection offline.

Requirements

- Python 3.9+
- A Vosk model for Russian (or another supported language)
- OpenAI API key (for Whisper endpoint)
- Spotify Developer credentials (client id / secret) and a redirect URI

Python dependencies

All runtime dependencies are listed in `requirements.txt`. At minimum you need:

- pyaudio
- vosk
- openai
- python-dotenv
- spotipy

Setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Download a Vosk model and unpack it under the project `model/` folder. Example project includes a Vosk model at `model/vosk-model-small-ru-0.22/`.

4. Create a `.env` file in the project root with the following variables:

```
WAKE_WORD=assistant
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
OPENAI_API_KEY=sk-...
VOSK_MODEL_PATH=model/vosk-model-small-ru-0.22
```

Usage

Run the assistant with:

```powershell
python main.py
```

How it works (short)

- The app listens using PyAudio and feeds audio to the Vosk recognizer.
- When the wake word (default: "assistant") is detected it records a short phrase, sends it to OpenAI Whisper for transcription, then uses the transcribed text to search Spotify and start playback on the first available device.

Notes and tips

- Vosk model directories are large. Keep the model under `model/` and set `VOSK_MODEL_PATH` accordingly.
- Microphone permissions are required. On Windows ensure the app has access to the microphone.
- For debugging, increase logging or print statements in `main.py`.

Security and privacy

- OpenAI audio transcription sends audio to OpenAI — do not use sensitive audio unless acceptable.
- Spotify tokens are stored via Spotipy's cache mechanism. Keep `.cache` files private.

Troubleshooting

- If Vosk model not found, verify `VOSK_MODEL_PATH` points to the unpacked model root that contains `am`, `conf`, and `graph` directories.
- If audio transcription fails, confirm `OPENAI_API_KEY` environment variable and that your account supports Whisper.
- If Spotify cannot start playback, ensure you have an active device and granted the requested scopes.

License

MIT License — feel free to use and adapt this project.

Contributing

PRs welcome. Open an issue to discuss major changes.
