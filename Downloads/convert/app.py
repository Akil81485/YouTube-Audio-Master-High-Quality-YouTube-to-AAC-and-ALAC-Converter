from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import yt_dlp
import os
import platform
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong secret key in production

# Directory to save downloads
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Music", "YouTubeDownloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def open_folder(path):
    """Open folder in file explorer, works for Windows, macOS, Linux."""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print(f"Could not open folder: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            flash("Please enter a YouTube video or playlist URL.")
            return redirect(url_for('index'))

        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'ignoreerrors': True,
            'extract_flat': True,  # Fetch metadata without downloading
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            flash(f"Error fetching info: {str(e)}")
            return redirect(url_for('index'))

        entries = info.get('entries')
        if entries is None:
            entries = [info]

        videos = []
        for entry in entries:
            if entry is None:
                continue
            videos.append({
                'id': entry.get('id'),
                'title': entry.get('title')
            })

        return render_template('select.html', videos=videos, url=url)

    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')

    if not url:
        flash("No URL provided for download.")
        return redirect(url_for('index'))

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'aac',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'keepvideo': False,
    }

    downloaded_files = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # info can be a playlist or single video
            if 'entries' in info:
                for entry in info['entries']:
                    if entry is None:
                        continue
                    filename = ydl.prepare_filename(entry)
                    filename = os.path.splitext(filename)[0] + '.aac'
                    if os.path.exists(filename):
                        downloaded_files.append(os.path.basename(filename))
            else:
                filename = ydl.prepare_filename(info)
                filename = os.path.splitext(filename)[0] + '.aac'
                if os.path.exists(filename):
                    downloaded_files.append(os.path.basename(filename))
    except Exception as e:
        flash(f"Error downloading: {str(e)}")
        return redirect(url_for('index'))

    # Open folder on your local machine after download completes
    open_folder(DOWNLOAD_DIR)

    return render_template('download.html', files=downloaded_files)

@app.route('/files/<filename>')
def files(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
