import yt_dlp
from pydub import AudioSegment
import os
import imageio_ffmpeg

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR,exist_ok = True)
try:
    ffmpeg_exe_path = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    ffmpeg_exe_path = None

def download_youtube_audio(url: str) -> str:
    output_tmpl = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")

    # Write cookie from Railway environment variable if set
    cookie_path = None
    yt_cookie_env = os.getenv("YOUTUBE_COOKIE")
    if yt_cookie_env:
        cookie_path = os.path.join(DOWNLOAD_DIR, "railway_yt_cookies.txt")
        # Format as netscape cookie header or pass raw
        with open(cookie_path, "w") as f:
            f.write(yt_cookie_env)

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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        wav_path = os.path.splitext(filename)[0] + ".wav"

    return wav_path

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