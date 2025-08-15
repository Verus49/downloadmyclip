from flask import Flask, request, Response
import yt_dlp
import io
import requests
from urllib.parse import urlparse
import mimetypes

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en" >
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DownloadMyClip - Social Video & Audio Downloader</title>
  <meta name="description" content="Download videos and audio from TikTok, Instagram, Facebook, YouTube, Twitter, and more. Save your favorite clips in MP4 or MP3 with DownloadMyClip." />
  <meta name="keywords" content="video downloader, audio downloader, TikTok download, Instagram reel downloader, Facebook video, YouTube mp4, Twitter video download" />
  <meta name="robots" content="index, follow" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

    /* Reset & base */
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      background: #000;
      color: #fff;
      font-family: 'Inter', sans-serif;
      font-weight: 400;
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    a {
      color: inherit;
      text-decoration: none;
    }

    /* Nav */
    nav {
      display: flex;
      gap: 2rem;
      font-weight: 700;
      font-size: 1rem;
      border-bottom: 1px solid #222;
      padding: 1rem 2rem;
      background: #000;
      justify-content: center;
      flex-wrap: wrap;
      user-select: none;
    }
    nav a {
      padding-bottom: 4px;
      border-bottom: 3px solid transparent;
      transition: border-color 0.3s ease;
      cursor: pointer;
      white-space: nowrap;
    }
    nav a:hover,
    nav a:focus {
      border-bottom-color: #fff;
      outline: none;
    }

    /* Main container */
    main {
      flex: 1;
      max-width: 600px;
      margin: 2rem auto 4rem;
      padding: 0 1rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    h1 {
      font-weight: 900;
      font-size: 3rem;
      letter-spacing: 0.1em;
      margin-bottom: 2rem;
      user-select: none;
      text-align: center;
    }

    form {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    input[type="url"] {
      background: transparent;
      border: 2px solid #444;
      color: #fff;
      padding: 1rem 1.25rem;
      font-size: 1.1rem;
      border-radius: 6px;
      transition: border-color 0.3s ease;
      outline-offset: 2px;
    }
    input[type="url"]:focus {
      border-color: #fff;
      outline: none;
    }

    .format-select {
      display: flex;
      justify-content: center;
      gap: 2rem;
      font-weight: 700;
      color: #bbb;
      user-select: none;
    }
    .format-select label {
      cursor: pointer;
      font-size: 1rem;
    }
    .format-select input[type="radio"] {
      accent-color: #fff;
      margin-right: 0.5rem;
      cursor: pointer;
      width: 18px;
      height: 18px;
      vertical-align: middle;
    }

    button[type="submit"] {
      background: #fff;
      color: #000;
      font-weight: 900;
      padding: 1rem 0;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 1.25rem;
      user-select: none;
      transition: background-color 0.3s ease;
      box-shadow: 0 0 8px #fff5;
    }
    button[type="submit"]:hover,
    button[type="submit"]:focus {
      background: #ddd;
      outline: none;
    }

    #loading {
      margin-top: 1.2rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.8rem;
      color: #fff;
      font-weight: 700;
      font-size: 1rem;
      user-select: none;
      visibility: hidden;
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    #loading.active {
      visibility: visible;
      opacity: 1;
    }

    #message {
      margin-top: 1rem;
      min-height: 1.3rem;
      color: #ff5555;
      font-weight: 600;
      text-align: center;
      user-select: none;
    }

    .spinner {
      width: 24px;
      height: 24px;
      border: 3px solid #fff;
      border-top: 3px solid transparent;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Footer */
    footer {
      background: #111;
      text-align: center;
      padding: 1rem 1rem;
      font-size: 0.85rem;
      color: #888;
      user-select: none;
      border-top: 1px solid #222;
    }
    footer nav a {
      color: #888;
      margin: 0 10px;
      text-decoration: none;
      font-weight: 700;
      cursor: pointer;
      transition: color 0.3s ease;
    }
    footer nav a:hover,
    footer nav a:focus {
      color: #fff;
      outline: none;
    }

    /* Ads placeholders */
    .ads {
      margin: 2rem 0;
      display: flex;
      justify-content: center;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .ad-slot {
      background: #222;
      padding: 1rem 1.5rem;
      border-radius: 8px;
      color: #666;
      font-size: 0.85rem;
      user-select: none;
      min-width: 280px;
      text-align: center;
      box-shadow: 0 0 6px #fff2;
    }

    @media (max-width: 640px) {
      nav {
        gap: 1rem;
        padding: 1rem;
      }
      .ads {
        flex-direction: column;
        gap: 1rem;
        margin: 1.5rem 0;
      }
      .ad-slot {
        min-width: 100%;
      }
    }
  </style>
</head>
<body>
<nav aria-label="Primary navigation">
  <a href="#" data-url="https://www.tiktok.com/@user/video/123456789" onclick="setExample(event)">TikTok</a>
  <a href="#" data-url="https://www.facebook.com/video.php?v=123456789" onclick="setExample(event)">Facebook</a>
  <a href="#" data-url="https://www.youtube.com/watch?v=abcdefg" onclick="setExample(event)">YouTube</a>
  <a href="#" data-url="https://www.instagram.com/reel/abcdefg/" onclick="setExample(event)">Instagram</a>
  <a href="#" data-url="https://twitter.com/user/status/123456789" onclick="setExample(event)">Twitter</a>
  <a href="#" data-url="https://vimeo.com/123456789" onclick="setExample(event)">Vimeo</a>
  <a href="#" onclick="openPopup('/static/about.html', 'About')" style="color: #888; margin-left: 20px;">About</a>
</nav>

<main>
  <h1>DownloadMyClip</h1>
  <form id="downloadForm" novalidate>
    <input
      type="url"
      name="url"
      id="urlInput"
      placeholder="Paste video URL here"
      required
      autocomplete="off"
      aria-label="Video URL input"
    />
    <div class="format-select" role="radiogroup" aria-label="Choose download format">
      <label><input type="radio" name="format" value="video" checked /> Video (MP4)</label>
      <label><input type="radio" name="format" value="audio" /> Audio (MP3)</label>
    </div>
    <button type="submit" id="downloadBtn">Download</button>
  </form>

  <div id="loading" aria-live="polite" role="status" aria-hidden="true">
    <div class="spinner" aria-hidden="true"></div>
    Downloading, please wait...
  </div>
  <div id="message" role="alert" aria-live="assertive"></div>

  <div class="ads" aria-label="Advertisement slots">
    <div class="ad-slot" aria-label="Top advertisement slot">Top Banner Ad Slot</div>
    <div class="ad-slot" aria-label="Bottom advertisement slot">Bottom Banner Ad Slot</div>
  </div>
</main>

<footer>
  <nav aria-label="Footer navigation">
    <a href="#" onclick="openPopup('/static/contact.html', 'Contact Us')">Contact Us</a> |
    <a href="#" onclick="openPopup('/static/terms.html', 'Terms of Service')">Terms of Service</a> |
    <a href="#" onclick="openPopup('/static/privacy.html', 'Privacy Policy')">Privacy Policy</a> |
    <a href="#" onclick="openPopup('/static/about.html', 'About')">About</a>
  </nav>
  <div style="margin-top: 0.5rem;">&copy; 2025 DownloadMyClip. All rights reserved.</div>
</footer>

<script>
  function setExample(event) {
    event.preventDefault();
    const url = event.target.getAttribute('data-url');
    const urlInput = document.getElementById('urlInput');
    urlInput.value = url || '';
    document.getElementById('message').textContent = '';
    urlInput.focus();
  }

  const form = document.getElementById('downloadForm');
  const loading = document.getElementById('loading');
  const message = document.getElementById('message');
  const downloadBtn = document.getElementById('downloadBtn');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    message.textContent = '';
    loading.classList.add('active');
    loading.setAttribute('aria-hidden', 'false');
    downloadBtn.disabled = true;

    const url = document.getElementById('urlInput').value.trim();
    const format = form.format.value;

    fetch('/stream', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, format}),
    })
    .then(response => {
      loading.classList.remove('active');
      loading.setAttribute('aria-hidden', 'true');
      downloadBtn.disabled = false;

      if (!response.ok) {
        return response.json().then(data => { throw new Error(data.error || 'Download failed'); });
      }
      const disposition = response.headers.get('Content-Disposition');
      let filename = 'download.' + (format === 'audio' ? 'mp3' : 'mp4');
      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/);
        if (match && match[1]) filename = match[1];
      }
      return response.blob().then(blob => ({blob, filename}));
    })
    .then(({blob, filename}) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    })
    .catch(err => {
      loading.classList.remove('active');
      loading.setAttribute('aria-hidden', 'true');
      downloadBtn.disabled = false;
      message.textContent = err.message;
    });
  });

  function openPopup(url, title) {
    const width = 600;
    const height = 600;
    const left = (screen.width / 2) - (width / 2);
    const top = (screen.height / 2) - (height / 2);
    window.open(url, title, `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes`);
  }
</script>
</body>
</html>
"""
@app.route('/')
def index():
    return INDEX_HTML

@app.route('/stream', methods=['POST'])
def stream_video():
    data = request.get_json()
    url = data.get('url', '').strip()
    format_type = data.get('format', 'video')

    if not url:
        return {"error": "No URL provided"}, 400

    try:
        # Check if it's a direct file (e.g., ends with .mp4, .webm, etc.)
        parsed = urlparse(url)
        if parsed.path.lower().endswith(('.mp4', '.webm', '.mkv', '.mov', '.avi')):
            return stream_direct(url, format_type)

        # Otherwise, use yt-dlp to extract stream URL
        ydl_opts = {
            'format': 'bestaudio/best' if format_type == 'audio' else 'best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')
            filename = (info.get('title') or "download").replace(" ", "_")
            ext = 'mp3' if format_type == 'audio' else info.get('ext', 'mp4')
            filename = f"{filename}.{ext}"
        
        return stream_direct(stream_url, format_type, filename)

    except Exception as e:
        return {"error": str(e)}, 500


def stream_direct(stream_url, format_type, filename=None):
    # Fallback filename
    if not filename:
        path = urlparse(stream_url).path
        filename = path.split("/")[-1] or f"download.{ 'mp3' if format_type == 'audio' else 'mp4' }"

    # Stream content in chunks
    r = requests.get(stream_url, stream=True)
    if r.status_code != 200:
        return {"error": f"Failed to fetch media: {r.status_code}"}, 400

    def generate():
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    return Response(
        generate(),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": mime_type
        }
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)

