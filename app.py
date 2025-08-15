from flask import Flask, request, Response, render_template_string, jsonify, send_from_directory
import yt_dlp
import requests
import os

app = Flask(__name__)

INDEX_HTML = """ 
<!-- your big Instagram theme HTML from before with footer updated for popup links -->
<!DOCTYPE html>
<html lang="en" >
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Social Video & Audio Downloader - Instagram Theme</title>
  <meta name="description" content="Download videos and reels from TikTok, Facebook, YouTube, Instagram, Twitter, and more — easily save your favorite clips in MP4 or audio format for personal use. Fast, secure, and free." />
  <meta name="keywords" content="video downloader, audio downloader, TikTok download, Facebook video download, YouTube mp4, Instagram reel download, Twitter video download" />
  <style>
  /* Keep all your previous CSS exactly as is */
  /* ... (omit for brevity) ... */
  /* Just add the spinner CSS for the loader */
  @keyframes spin {
      to {transform: rotate(360deg);}
  }
  </style>
</head>
<body>
<nav aria-label="Primary navigation">
  <a href="#" data-url="https://www.tiktok.com/@someuser/video/123456" onclick="setExample(event)">TikTok</a>
  <a href="#" data-url="https://www.facebook.com/video.php?v=123456" onclick="setExample(event)">Facebook</a>
  <a href="#" data-url="https://www.youtube.com/watch?v=abcdef" onclick="setExample(event)">YouTube</a>
  <a href="#" data-url="https://www.instagram.com/reel/abcdefg/" onclick="setExample(event)">Instagram</a>
  <a href="#" data-url="https://twitter.com/user/status/123456" onclick="setExample(event)">Twitter</a>
  <a href="#" data-url="https://vimeo.com/123456" onclick="setExample(event)">Vimeo</a>
  <a href="/about.html" style="color:#f58529; margin-left: 20px;">About</a>
</nav>

<div class="page-wrapper" role="main">
  <header>
    <div class="ad-slot ad-top" aria-label="Top banner advertisement">
      Responsive Top Banner Ad Slot
    </div>
  </header>

  <aside class="ad-left" aria-label="Left sidebar advertisements">
    <div class="ad-slot" aria-label="Left sidebar ad 1">Left Sidebar Ad 1</div>
    <div class="ad-slot" aria-label="Left sidebar ad 2">Left Sidebar Ad 2</div>
  </aside>

  <main>
    <h1>Social Video & Audio Downloader</h1>
    <form id="downloadForm" novalidate>
      <input type="url" name="url" id="urlInput" placeholder="Paste video URL here" required autocomplete="off" aria-label="Video URL input" />
      <div class="format-select" role="radiogroup" aria-label="Choose download format">
        <label><input type="radio" name="format" value="video" checked /> Video (MP4)</label>
        <label><input type="radio" name="format" value="audio" /> Audio (MP3)</label>
      </div>
      <button type="submit" id="downloadBtn">Download</button>
    </form>

    <div id="loading" aria-live="polite" role="status" style="display:none;">
      <div class="spinner"></div>
      Downloading, please wait...
    </div>
    <div id="message" role="alert" aria-live="assertive"></div>

    <p class="seo-text">
      Download videos and reels from TikTok, Facebook, YouTube, Instagram, Twitter, and more — easily save your favorite clips in MP4 or audio format for personal use. Fast, secure, and free.
    </p>
  </main>

  <aside class="ad-right" aria-label="Right sidebar advertisements">
    <div class="ad-slot" aria-label="Right sidebar ad 1">Right Sidebar Ad 1</div>
    <div class="ad-slot" aria-label="Right sidebar ad 2">Right Sidebar Ad 2</div>
  </aside>

  <footer>
    <div class="ad-slot ad-bottom" aria-label="Bottom banner advertisement">
      Responsive Bottom Banner Ad Slot
    </div>
    <nav aria-label="Footer navigation" style="margin-top: 1rem; font-size: 0.9rem; text-align:center;">
      <a href="#" onclick="openPopup('/contact.html', 'Contact Us')"
         style="color:#bbb; margin:0 10px; text-decoration:none;">Contact Us</a> |
      <a href="#" onclick="openPopup('/terms.html', 'Terms of Service')"
         style="color:#bbb; margin:0 10px; text-decoration:none;">Terms of Service</a> |
      <a href="#" onclick="openPopup('/privacy.html', 'Privacy Policy')"
         style="color:#bbb; margin:0 10px; text-decoration:none;">Privacy Policy</a>
    </nav>
    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #555;">
      &copy; 2025 YourSiteName. All rights reserved.
    </div>
  </footer>
</div>

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
    loading.style.display = 'block';
    downloadBtn.disabled = true;

    const url = document.getElementById('urlInput').value.trim();
    const format = form.format.value;

    fetch('/stream', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, format}),
    })
    .then(response => {
      loading.style.display = 'none';
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
      loading.style.display = 'none';
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

def get_direct_url(video_url, fmt):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best' if fmt == 'audio' else 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        if fmt == 'audio':
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if not audio_formats:
                return info.get('url')
            best_audio = sorted(audio_formats, key=lambda f: f.get('abr', 0), reverse=True)[0]
            return best_audio['url']
        else:
            return info.get('url')


@app.route('/', methods=['GET'])
def index():
    return render_template_string(INDEX_HTML)

@app.route('/stream', methods=['POST'])
def stream():
    data = request.get_json(force=True)
    url = data.get('url', '').strip()
    fmt = data.get('format', 'video')

    if not url:
        return jsonify(error="No URL provided"), 400
    if fmt not in ('video', 'audio'):
        return jsonify(error="Invalid format"), 400

    try:
        direct_url = get_direct_url(url, fmt)
    except Exception as e:
        return jsonify(error=f"Failed to extract direct URL: {str(e)}"), 500

    if not direct_url:
        return jsonify(error="Could not find direct media URL"), 404

    def generate():
        try:
            with requests.get(direct_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
        except requests.RequestException:
            return

    ext = 'mp3' if fmt == 'audio' else 'mp4'
    filename = f"download.{ext}"
    mimetype = 'audio/mpeg' if fmt == 'audio' else 'video/mp4'

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "no-cache",
    }

    return Response(generate(), headers=headers, mimetype=mimetype)

# Serve static html pages (contact.html, terms.html, privacy.html)
@app.route('/<path:filename>')
def static_html(filename):
    allowed = {'contact.html', 'terms.html', 'privacy.html'}
    if filename in allowed:
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)
    return "Not found", 404


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting downloader on port {port}...")
    app.run(host='0.0.0.0', port=port)
