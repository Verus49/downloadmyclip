from flask import Flask, request, Response
import yt_dlp
import requests
import re

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Video Downloader</title>
    <style>
        body {
            background-color: #fafafa;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        h1 {
            font-family: 'Billabong', cursive;
            font-size: 48px;
            color: #262626;
            margin-bottom: 20px;
        }
        form {
            background: #fff;
            padding: 20px;
            border: 1px solid #dbdbdb;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            width: 320px;
        }
        input, select, button {
            margin: 5px 0;
            padding: 10px;
            font-size: 14px;
            border: 1px solid #dbdbdb;
            border-radius: 4px;
        }
        button {
            background-color: #0095f6;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #007acc;
        }
    </style>
</head>
<body>
    <h1>VidGram</h1>
    <form action="/download" method="get">
        <input type="url" name="url" placeholder="Enter video URL" required>
        <select name="type">
            <option value="video">Video (MP4)</option>
            <option value="audio">Audio (MP3)</option>
        </select>
        <button type="submit">Download</button>
    </form>
</body>
</html>
"""

VIDEO_PATTERN = re.compile(r".*\.(mp4|webm|mkv|mov|m3u8)(\?.*)?$", re.IGNORECASE)

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/download')
def download():
    url = request.args.get('url')
    download_type = request.args.get('type', 'video')

    if not url:
        return "No URL provided", 400

    try:
        if VIDEO_PATTERN.match(url):
            # Direct file streaming
            return stream_direct(url, download_type)
        else:
            # Use yt-dlp
            return stream_ytdlp(url, download_type)
    except Exception as e:
        return f"Error: {str(e)}", 500

def stream_direct(url, download_type):
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        return f"Failed to fetch file: {r.status_code}", 400

    content_type = 'video/mp4' if download_type == 'video' else 'audio/mpeg'
    filename = 'download.mp4' if download_type == 'video' else 'download.mp3'

    return Response(
        r.iter_content(chunk_size=8192),
        content_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

def stream_ytdlp(url, download_type):
    ydl_opts = {
        'format': 'bestaudio/best' if download_type == 'audio' else 'best',
        'quiet': True,
        'noplaylist': True,
        'outtmpl': '-',
    }
    if download_type == 'audio':
        ydl_opts.update({
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })

    def generate():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            direct_url = result['url']
            r = requests.get(direct_url, stream=True)
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk

    content_type = 'audio/mpeg' if download_type == 'audio' else 'video/mp4'
    filename = 'download.mp3' if download_type == 'audio' else 'download.mp4'

    return Response(
        generate(),
        content_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
