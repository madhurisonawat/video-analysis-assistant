import yt_dlp
from pydub import AudioSegment
import re
import os
import imageio_ffmpeg
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

try:
    ffmpeg_exe_path = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    ffmpeg_exe_path = None


def extract_video_id(url: str) -> str:
    """Extract 11-character YouTube video ID."""
    match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else url


def fetch_youtube_transcript_text(video_id: str) -> str:
    """Fetch text transcript directly without downloading audio files."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "hi", "en-IN"]
        )
        return " ".join([item["text"] for item in transcript_list])
    except Exception as e:
        print(f"Transcript fetch error: {e}")
        return None


def download_youtube_audio(url: str) -> str:
    output_tmpl = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    cookie_path = None

    yt_cookie_env = os.getenv("YOUTUBE_COOKIE")
    if yt_cookie_env:
        cookie_path = os.path.join(DOWNLOAD_DIR, "railway_yt_cookies.txt")
        try:
            clean_b64 = yt_cookie_env.strip().replace("\n", "").replace("\r", "")
            missing_padding = len(clean_b64) % 4
            if missing_padding:
                clean_b64 += "=" * (4 - missing_padding)

            decoded_bytes = base64.b64decode(clean_b64)
            with open(cookie_path, "wb") as f:
                f.write(decoded_bytes)
        except Exception as e:
            print(f"Error decoding YOUTUBE_COOKIE: {e}")
            cookie_path = None

    ydl_opts = {
        "format": "bestaudio/best/ba/b",
        "outtmpl": output_tmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }

    if ffmpeg_exe_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_exe_path

    if cookie_path and os.path.exists(cookie_path):
        ydl_opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            wav_path = os.path.splitext(filename)[0] + ".wav"
            return wav_path
    except Exception as e:
        print(f"Audio download blocked by YouTube ({e}). Attempting transcript API fallback...")
        video_id = extract_video_id(url)
        transcript_text = fetch_youtube_transcript_text(video_id)
        if transcript_text:
            # Return raw text string flag or save to temporary text file
            txt_path = os.path.join(DOWNLOAD_DIR, f"{video_id}_transcript.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            return txt_path
        raise e
def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path



def chunk_audio(wav_path : str , chunk_minutes : int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0,len(audio),chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path , format = "wav")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks