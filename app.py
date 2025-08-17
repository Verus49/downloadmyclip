from __future__ import annotations
import os
import re
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import unquote

from flask import Flask, jsonify, render_template_string, request, send_file
import yt_dlp

INDEX_HTML = r"""<!DOCTYPE html>
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

app = Flask(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

SAFE_VIDEO_EXTS = {"mp4", "webm", "mkv", "mov"}
SAFE_AUDIO_EXTS = {"mp3", "m4a", "webm", "opus", "aac", "wav", "ogg"}

def sanitize_filename(name: str) -> str:
    name = unquote(name or "").strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = name.strip().strip(".")
    return name or "download"

def _guess_mime(ext: str) -> str:
    ext = (ext or "").lower()
    return {
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mkv": "video/x-matroska",
        "mov": "video/quicktime",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "opus": "audio/opus",
        "ogg": "audio/ogg",
        "wav": "audio/wav",
    }.get(ext, "application/octet-stream")

def _make_tmpdir() -> Path:
    base = Path(os.getenv("TMPDIR", "/tmp"))
    d = base / f"dmc_{uuid.uuid4().hex}"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _cleanup_dir(path: Path):
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

def download_with_ytdlp(url: str, want_audio: bool, cookies_file: str | None = None) -> tuple[Path, str, str]:
    tmpdir = _make_tmpdir()
    outtmpl = "%(title).200B.%(ext)s"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "restrictfilenames": False,
        "windowsfilenames": False,
        "geo_bypass": True,
        "http_headers": {"User-Agent": DEFAULT_UA, "Accept-Language": "en-US,en;q=0.9"},
        "paths": {"home": str(tmpdir)},
        "outtmpl": {"default": outtmpl},
        "merge_output_format": "mp4" if not want_audio else None,
        "retries": 3,
        "concurrent_fragment_downloads": 1,
    }

    if cookies_file and os.path.exists(cookies_file):
        ydl_opts["cookiefile"] = cookies_file

    if want_audio:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio","preferredcodec": "mp3","preferredquality": "192",}]
    else:
        ydl_opts["format"] = (
            "bestvideo[ext=mp4][vcodec~='^((?!av01|vp9).)*$'][height<=1080]+bestaudio[ext=m4a]/"
            "best[ext=mp4]/best"
        )

    info = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        _cleanup_dir(tmpdir)
        raise RuntimeError(f"{str(e).strip()}")

    candidates = sorted(
        (p for p in tmpdir.rglob("*") if p.is_file()),
        key=lambda p: (p.stat().st_mtime, p.stat().st_size),
        reverse=True,
    )

    if not candidates:
        _cleanup_dir(tmpdir)
        raise RuntimeError("Download completed but no file was produced.")

    chosen = None
    for p in candidates:
        ext = p.suffix.lower().lstrip(".")
        if want_audio and ext in SAFE_AUDIO_EXTS:
            chosen = p
            break
        if not want_audio and ext in SAFE_VIDEO_EXTS:
            chosen = p
            break
    if chosen is None:
        chosen = candidates[0]

    title = sanitize_filename((info.get("title") or "download").strip())
    ext = chosen.suffix.lstrip(".").lower()
    dl_name = f"{title}.{ext}"
    mime = _guess_mime(ext)

    return chosen, dl_name, mime

@app.route("/", methods=["GET"])
def index_route():
    return render_template_string(INDEX_HTML)

@app.route("/healthz")
def healthz():
    return "ok", 200

@app.route("/upload_cookies", methods=["POST"])
def upload_cookies():
    data = request.get_json(silent=True) or {}
    site = data.get("site")
    cookies = data.get("cookies")
    if not site or not cookies:
        return jsonify({"error": "Missing site or cookies"}), 400
    filename = f"cookies_{site}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write(cookies)
    return jsonify({"status":"ok","file":filename})

@app.route("/stream", methods=["POST"])
def stream():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    fmt = (data.get("format") or "video").strip().lower()
    if not url or not re.match(r"^https?://", url):
        return jsonify(error="Please enter a valid http(s) URL."), 400
    if fmt not in {"video","audio"}:
        return jsonify(error="Invalid format; choose video or audio."), 400
    want_audio = (fmt=="audio")
    cookies_file = None
    for s in ("tiktok.com","youtube.com","instagram.com","facebook.com"):
        candidate = f"cookies_{s}.txt"
        if os.path.exists(candidate):
            cookies_file = candidate
            break
    try:
        filepath, dl_name, mime = download_with_ytdlp(url, want_audio=want_audio, cookies_file=cookies_file)
    except Exception as e:
        msg = str(e)
        if "This content isn" in msg or "Video unavailable" in msg:
            return jsonify(error="This video is unavailable or blocked in your region."), 400
        return jsonify(error=f"Could not download this link: {msg}"), 400
    tmp_root = filepath.parent
    try:
        response = send_file(
            path_or_file=str(filepath),
            mimetype=mime,
            as_attachment=True,
            download_name=dl_name,
            conditional=True,
            max_age=0,
            etag=False,
            last_modified=None,
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{dl_name}"
        response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        try:
            time.sleep(0.5)
            _cleanup_dir(tmp_root)
        except Exception:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT","8000"))
    app.run(host="0.0.0.0", port=port)
