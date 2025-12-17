import subprocess
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

def get_audio_stream(video_id: str):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # 1. Get the URL of the best audio stream
    # We use yt-dlp to dump json and parse it, or just use -g to get the url
    # Using 'g' (get-url) is faster. -f bestaudio ensures we get audio.
    # We will pipe this URL into ffmpeg.
    
    # Command to get audio URL
    yt_cmd = [
        "yt-dlp",
        "-g",
        "-f", "bestaudio",
        video_url
    ]
    
    try:
        audio_source_url = subprocess.check_output(yt_cmd).decode("utf-8").strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting URL from yt-dlp: {e}")
        return None

    # 2. Convert to MP3 64k using ffmpeg and stream to stdout
    # -i <url> : input
    # -vn : no video
    # -acodec libmp3lame : mp3 codec
    # -ab 64k : audio bitrate 64k
    # -f mp3 : format mp3
    # pipe:1 : output to stdout
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", audio_source_url,
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "64k",
        "-f", "mp3",
        "pipe:1"
    ]
    
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return process.stdout

@app.get("/mp3/{video_id}")
async def stream_mp3(video_id: str):
    # This is a generator that yield chunks of data
    audio_stream = get_audio_stream(video_id)
    
    if not audio_stream:
        return Response(content="Error processing video", status_code=500)

    def iterfile():
        while True:
            data = audio_stream.read(4096)
            if not data:
                break
            yield data
            
    headers = {
        'Content-Disposition': f'attachment; filename="{video_id}.mp3"'
    }
    
    return Response(content=iterfile(), media_type="audio/mpeg", headers=headers)

@app.get("/")
async def index():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
