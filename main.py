import subprocess
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

import yt_dlp

# Changed to 'def' (sync) so FastAPI runs it in a thread pool, preventing event loop blocking
@app.get("/mp3/{video_id}")
def stream_mp3(video_id: str):
    print(f"Processing video: {video_id}")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'socket_timeout': 10,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            audio_source_url = info['url']
            
    except Exception as e:
        return Response(content=f"Error extracting URL ({type(e).__name__}): {str(e)}", status_code=500)

    # 2. Convert to MP3 64k using ffmpeg and stream to stdout
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", audio_source_url,
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "64k",
        "-f", "mp3",
        "pipe:1"
    ]
    
    # We use a try/finally block or similar if we wanted to be safer, 
    # but for a simple stream, this is okay.
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    def iterfile():
        try:
            while True:
                data = process.stdout.read(4096)
                if not data:
                    break
                yield data
        except Exception:
            pass
        finally:
            process.stdout.close()
            process.wait()
            
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
