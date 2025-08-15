from flask import Flask, request, Response, render_template_string, jsonify, send_from_directory
import yt_dlp
import requests
import os
import re
from urllib.parse import urlparse, unquote

app = Flask(__name__)

# ---- Config ----
DIRECT_VIDEO_EXTS = ('.mp4', '.webm', '.mkv', '.mov')
DIRECT_AUDIO_EXTS = ('.mp3', '.m4a', '.aac', '.wav', '.ogg')
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0 Safari/537.36"
)
REQUEST_TIMEOUT = (10, 30)  # (connect, read) seconds
CHUNK = 1024 * 256  # 256 KB

# ---- HTML (kept, lightly polished) ----
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
    * { box-sizing: border-box; }
    body {
      margin: 0; background: #000; color: #fff; font-family: 'Inter', sans-serif;
      line-height: 1.5; min-height: 100vh; display: flex; flex-direction: column;
      -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
    }
    a { color: inherit; text-decoration: none; }
    nav {
      display: flex; gap: 1.25rem; font-weight: 700; font-size: 0.95rem;
      border-bottom: 1px solid #222; padding: 1rem 1.25rem; background: #000;
      justify-content: center; flex-wrap: wrap; user-select: none;
      position: sticky; top: 0; z-index: 10;
    }
    nav a { padding-bottom: 4px; border-bottom: 3px solid transparent; transition: border-color .2s; }
    nav a:hover, nav a:focus { border-bottom-color: #fff; outline: none; }
    main { flex: 1; max-width: 640px; margin: 2rem auto 4rem; padding: 0 1rem; display: flex; flex-direction: column; align-items: center; }
    h1 { font-weight: 900; font-size: clamp(2.2rem, 5vw, 3rem); letter-spacing: 0.06em; margin-bottom: 1.5rem; user-select: none; text-align: center; }
    form { width: 100%; display: flex; flex-direction: column; gap: 1rem; }
    input[type="url"] {
      background: #0b0b0b; border: 2px solid #2b2b2b; color: #fff; padding: 1rem 1.1rem;
      font-size: 1.05rem; border-radius: 10px; transition: border-color .2s, box-shadow .2s;
    }
    input[type="url"]::placeholder { color: #888; }
    input[type="url"]:focus { border-color: #fff; outline: none; box-shadow: 0 0 0 4px #ffffff1a; }
    .format-select { display: flex; justify-content: center; gap: 1.5rem; font-weight: 700; color: #bbb; user-select: none; }
    .format-select label { cursor: pointer; font-size: 0.95rem; }
    .format-select input[type="radio"] { accent-color: #fff; margin-right: .5rem; cursor: pointer; width: 18px; height: 18px; vertical-align: middle; }
    button[type="submit"] {
      background: #fff; color: #000; font-weight: 900; padding: 1rem 0; border: none;
      border-radius: 10px; cursor: pointer; font-size: 1.15rem; user-select: none;
      transition: transform .05s ease, background-color .2s; box-shadow: 0 0 12px #fff4;
    }
    button[type="submit"]:active { transform: translateY(1px); }
    button[type="submit"]:hover, button[type="submit"]:focus { background: #e6e6e6; outline: none; }
    #loading {
      margin-top: .6rem; display: flex; align-items: center; justify-content: center; gap: .6rem;
      color: #fff; font-weight: 700; font-size: .95rem; user-select: none; visibility: hidden; opacity: 0; transition: opacity .2s;
    }
    #loading.active { visibility: visible; opacity: 1; }
    #message { margin-top: .75rem; min-height: 1.3rem; color: #ff6666; font-weight: 700; text-align: center; user-select: none; }
    .spinner { width: 22px; height: 22px; border: 3px solid #fff; border-top: 3px solid transparent; border-radius: 50%; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    footer { background: #111; text-align: center; padding: 1rem; font-size: .85rem; color: #888; user-select: none; border-top: 1px solid #222; }
    footer nav a { color: #888; margin: 0 10px; font-weight: 700; transition: color .2s; }
    footer nav a:hover, footer nav a:focus { color: #fff; outline: none; }
    .ads { margin: 2rem 0; display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; }
    .ad-slot { background: #171717; padding: 1rem 1.25rem; border-radius: 10px; color: #666; font-size: .85rem; user-select: none; min-width: 260px; text-align: center; box-shadow: 0 0 6px #fff2; }
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
    <input type="url" name="url" id="urlInput" placeholder="Paste video or audio URL here (MP4, MP3, social links…)" required autocomplete="off" aria-label="Video URL input"/>
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
    .then(async (response) => {
      loading.classList.remove('active');
      loading.setAttribute('aria-hidden', 'true');
      downloadBtn.disabled = false;

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || 'Download failed');
      }
      const disposition = response.headers.get('Content-Disposition');
      const ct = response.headers.get('Content-Type') || '';
      const isAudio = ct.includes('audio');
      let filename = 'download.' + (isAudio ? 'mp3' : 'mp4');
      if (disposition) {
        const match = disposition.match(/filename\\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?/);
        if (match) filename = decodeURIComponent(match[1] || match[2]);
      }
      const blob = await response.blob();
      const dlUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = dlUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(dlUrl);
    })
    .catch(err => {
      loading.classList.remove('active');
      loading.setAttribute('aria-hidden', 'true');
      downloadBtn.disabled = false;
      message.textContent = err.message;
    });
  });

  function openPopup(url, title) {
    const width = 600, height = 600;
    const left = (screen.width / 2) - (width / 2);
    const top = (screen.height / 2) - (height / 2);
    window.open(url, title, `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes`);
  }
</script>
</body>
</html>
"""

# ---------- Helpers ----------

def valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def is_direct_media(url: str, fmt: str) -> bool:
    u = url.lower()
    if fmt == "audio":
        return u.endswith(DIRECT_AUDIO_EXTS)
    # prefer progressive MP4/WebM/etc for video
    return u.endswith(DIRECT_VIDEO_EXTS)

def filename_from_url(url: str, fallback: str) -> str:
    try:
        path = urlparse(url).path
        name = os.path.basename(path)
        name = unquote(name)
        if name and re.search(r"\\.[a-z0-9]{2,5}$", name, re.I):
            return sanitize_filename(name)
    except Exception:
        pass
    return sanitize_filename(fallback)

def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = name.strip().strip(".")
    return name or "download"

def pick_best_format(info: dict, want_audio: bool):
    """
    Choose a progressive (single-file) format if possible (prefer mp4/m4a).
    Fallback to yt-dlp's top URL otherwise.
    """
    fmts = info.get("formats") or []
    if not fmts:
        return info.get("url"), info.get("ext") or ("mp3" if want_audio else "mp4"), info.get("acodec"), info.get("vcodec")

    # Filter for progressive single-file formats (no separate video/audio)
    progressive = []
    for f in fmts:
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        if want_audio:
            if (acodec and acodec != "none") and (not vcodec or vcodec == "none"):
                progressive.append(f)
        else:
            # Prefer formats that have both audio and video (vcodec != none and acodec != none)
            if (vcodec and vcodec != "none") and (acodec and acodec != "none"):
                progressive.append(f)

    def score(f):
        # prefer mp4/m4a, higher tbr/abr, https
        ext = (f.get("ext") or "").lower()
        bonus = 0
        if want_audio and ext in ("m4a", "mp3", "aac"):
            bonus += 50
        if not want_audio and ext in ("mp4", "webm"):
            bonus += 50
        if (f.get("protocol") or "").startswith("https"):
            bonus += 5
        return (f.get("tbr") or f.get("abr") or 0) + bonus

    best = None
    if progressive:
        best = max(progressive, key=score)
    else:
        # fallback: let yt-dlp decide (best/bestaudio)
        best = max(fmts, key=lambda f: f.get("tbr") or f.get("abr") or 0)

    return best.get("url"), best.get("ext") or ("mp3" if want_audio else "mp4"), best.get("acodec"), best.get("vcodec")

def get_via_ytdlp(source_url: str, fmt: str):
    """Use yt-dlp to extract a direct media URL suitable for streaming."""
    want_audio = (fmt == "audio")
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "http_headers": {"User-Agent": DEFAULT_UA, "Accept-Language": "en-US,en;q=0.9"},
        "extractor_args": {"youtube": {"player_client": ["web"]}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(source_url, download=False)
        # When yt-dlp gives a top-level URL, use that; else choose format.
        if want_audio:
            direct_url, ext, ac, vc = pick_best_format(info, want_audio=True)
            filename_base = info.get("title") or "downloadmyclip"
            return direct_url, f"{sanitize_filename(filename_base)}.mp3", "audio/mpeg"
        else:
            direct_url, ext, ac, vc = pick_best_format(info, want_audio=False)
            # prefer mp4 naming
            ext_final = "mp4" if (ext or "").lower() not in ("mp4", "webm") else ext.lower()
            filename_base = info.get("title") or "downloadmyclip"
            content_type = "video/mp4" if ext_final == "mp4" else "video/webm"
            return direct_url, f"{sanitize_filename(filename_base)}.{ext_final}", content_type

def proxy_stream(direct_url: str, filename: str, content_type: str, referer: str = None):
    """
    Stream bytes from direct_url to the client, passing Range through for seeking.
    """
    headers = {"User-Agent": DEFAULT_UA}
    if referer:
        headers["Referer"] = referer

    # Pass Range header for partial requests (seeking)
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    # Use stream=True and don't buffer whole file
    upstream = requests.get(direct_url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)

    # Determine status (200 or 206) and length
    status = upstream.status_code
    resp_headers = {
        "Content-Type": content_type,
        "Content-Disposition": f"attachment; filename*=UTF-8''{requests.utils.requote_uri(filename)}",
        "Cache-Control": "no-cache",
    }

    # Pass through size and range info if available
    if "Content-Length" in upstream.headers:
        resp_headers["Content-Length"] = upstream.headers["Content-Length"]
    if "Accept-Ranges" in upstream.headers:
        resp_headers["Accept-Ranges"] = upstream.headers["Accept-Ranges"]
    else:
        # Many CDNs support it even if not declared; be conservative:
        resp_headers["Accept-Ranges"] = "bytes"
    if "Content-Range" in upstream.headers:
        resp_headers["Content-Range"] = upstream.headers["Content-Range"]

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=CHUNK):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    return Response(generate(), headers=resp_headers, status=status)

# ---------- Routes ----------

@app.route('/', methods=['GET'])
def index():
    return render_template_string(INDEX_HTML)

@app.route('/stream', methods=['POST'])
def stream():
    data = request.get_json(force=True) or {}
    url = (data.get('url') or '').strip()
    fmt = (data.get('format') or 'video').strip().lower()

    if not url or not valid_url(url):
        return jsonify(error="Please enter a valid http(s) URL."), 400
    if fmt not in ('video', 'audio'):
        return jsonify(error="Invalid format; choose video or audio."), 400

    # 1) Direct link? stream without yt-dlp
    if is_direct_media(url, fmt):
        # Guess content-type & filename
        is_audio = (fmt == "audio") or url.lower().endswith(DIRECT_AUDIO_EXTS)
        content_type = "audio/mpeg" if is_audio else "video/mp4"
        default_name = "downloadmyclip.mp3" if is_audio else "downloadmyclip.mp4"
        filename = filename_from_url(url, default_name)
        return proxy_stream(url, filename, content_type, referer=url)

    # 2) Not direct → use yt-dlp to extract best streamable URL
    try:
        direct_url, filename, content_type = get_via_ytdlp(url, fmt)
    except yt_dlp.utils.DownloadError as e:
        # Specific yt-dlp error
        return jsonify(error=f"Could not extract media from this link: {e.exc_info[1] if hasattr(e, 'exc_info') else str(e)}"), 400
    except Exception as e:
        return jsonify(error=f"Failed to process URL: {str(e)}"), 500

    # Safety fallback filename/content-type
    if not filename:
        filename = "downloadmyclip.mp3" if fmt == "audio" else "downloadmyclip.mp4"
    if not content_type:
        content_type = "audio/mpeg" if fmt == "audio" else "video/mp4"

    return proxy_stream(direct_url, filename, content_type, referer=url)

@app.route('/static/<path:filename>')
def serve_static(filename):
    # Optional: serve auxiliary pages if you add them later
    static_dir = os.path.join(app.root_path, 'static')
    return send_from_directory(static_dir, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
