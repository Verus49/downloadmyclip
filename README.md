DownloadMyClip package ready for GitHub + Render deployment.

Files:
- app.py
- requirements.txt
- Procfile
- extension/ (Chrome extension to upload cookies)



Steps to deploy:
1) Replace BACKEND_URL in extension/background.js with your Render app URL + /upload_cookies
2) Zip and upload to GitHub, or push the folder to a repo.
3) On Render, create a Web Service connected to the repo. Set start command to the Procfile or use:
   gunicorn app:app --bind 0.0.0.0:$PORT --timeout 180
4) Optionally install ffmpeg on the server for MP3 conversion.
