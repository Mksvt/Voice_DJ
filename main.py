"""Voice-Activated Music Assistant"""
import os
import json
import pyaudio
import tempfile
import wave
import openai
from typing import cast
from dotenv import load_dotenv
import spotipy  # type: ignore
from vosk import Model, KaldiRecognizer  # type: ignore
from spotipy.oauth2 import SpotifyOAuth  # type: ignore

try:
    load_dotenv()
except ImportError as e:
    print(f"Error loading .env file: {e}")


WAKE_WORD = os.getenv("WAKE_WORD", "assistant")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "model")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

def record_phrase(stream: pyaudio.Stream, seconds: float = 5) -> bytes:
    """Records audio from the stream for a given duration."""
    frames = []
    for _ in range(int(16000/4000 * seconds)):
        data = stream.read(4000, exception_on_overflow=False)
        frames.append(data)
    return b''.join(frames)

def search_and_play(sp: spotipy.Spotify, query: str):
    """
    Searches for a track on Spotify using the provided query and plays the first result.

    Args:
        sp: An authenticated Spotipy client instance.
        query: The search query (e.g., song title and artist).

    Returns:
        True if the track was found and playback started, False otherwise.
    """
    try:
        results = sp.search(q=query, type="track", limit=1)
        if results["tracks"]["items"]:
            track = results["tracks"]["items"][0]
            devices = sp.devices()

            if devices and devices["devices"]:
                device_id = devices["devices"][0]["id"]
                sp.start_playback(device_id=device_id, uris=[track["uri"]])
                print(f"Playing '{track['name']}' by {track['artists'][0]['name']}.")
                return True
            else:
                print("No active Spotify device found.")
                return False
        else:
            print(f"No results found for '{query}'.")
            return False

    except Exception as e:
        print(f"Error searching and playing track: {e}")
        return False

def transcribe(data: bytes) -> str:
    """
    Transcribes the given audio data using OpenAI's Whisper model.

    The function saves the raw audio data to a temporary WAV file,
    sends it to the OpenAI API for transcription, and then deletes
    the temporary file.

    Args:
        data: A bytes object containing the raw audio data (16-bit, 16kHz, mono).

    Returns:
        The transcribed text as a string.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        tempfile_name = temp_file.name
    wav_file = cast(wave.Wave_write, wave.open(tempfile_name, "wb"))
    try:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(data)
    finally:
        wav_file.close()

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Open the WAV file in binary mode when sending to OpenAI
    with open(tempfile_name, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ru"
        )

    os.unlink(tempfile_name)
    return transcript.text.strip()

def listen_for_wake_word(recognizer : KaldiRecognizer, stream: pyaudio.Stream) -> None:
    """Listen for the wake word."""
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result()).get("text", "")
            if WAKE_WORD in result.lower():
                print("Wake word detected.")
                return
        partial = recognizer.PartialResult()
        if partial and len(partial) > 100:
            print(f"Partial: {partial}")
            recognizer.Reset()


def init_spotify_client():
    """Initialize and return a Spotify client."""
    scope = "user-read-playback-state,user-modify-playback-state"
    sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                            client_secret=SPOTIFY_CLIENT_SECRET,
                            redirect_uri=SPOTIFY_REDIRECT_URI,
                            scope=scope,
                            open_browser=True) # Changed to automatically open browser
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        # This will now open a browser and wait for the user to authenticate
        # The redirect will be handled automatically by Spotipy if a local server is available
        # or it will prompt for the URL if it cannot.
        # For this to work seamlessly, ensure you have a web server (like Flask or Django)
        # or use a simple http.server if needed, but Spotipy often handles this.
        token_info = sp_oauth.get_access_token(as_dict=False)

    return spotipy.Spotify(auth=token_info)

def main() -> None:
    """Main function to run the voice assistant."""
    if not os.path.exists(VOSK_MODEL_PATH):
        print(f"Please download the Vosk model and unpack it to the '{VOSK_MODEL_PATH}' directory.")
        return

    model = Model(VOSK_MODEL_PATH)
    spotify_client = init_spotify_client()
    if not spotify_client:
        return
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=4000)
    recognizer = KaldiRecognizer(model, 16000)

    print("Voice assistant is running...")

    try:
        while True:
            listen_for_wake_word(recognizer, stream)
            print("Listening for command...")
            data = record_phrase(stream)
            text = transcribe(data)
            print(text)
            search_and_play(spotify_client, text)
    except KeyboardInterrupt:
        print("Voice assistant stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()
