from __future__ import unicode_literals
import os
import threading
import re

from flask import Flask, render_template, request, flash, send_from_directory

# init vars for app
filepath = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(filepath, 'uploads')
app.config['STATIC_FOLDER'] = os.path.join(filepath, 'static')
app.config['TEMPLATE_FOLDER'] = os.path.join(filepath, 'templates')
app.secret_key = 'DDD'


@app.route('/', methods=['GET', 'POST'])
def index():
    # scan upload folder for existing videos
    videos = [
        f[:-4] for f in os.listdir(app.config['UPLOAD_FOLDER'])
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f)) and len(f) <= 15
    ]

    if request.method == 'POST':
        address = request.form['vidlink']

        if 'youtu.be' in address:
            idx = address.rfind('/')
            vidid = address[idx + 1:]
            vidlink = 'https://www.youtube.com/watch?v=' + vidid
        else:
            vidid = re.search(r'v=([a-zA-Z0-9\_\-]+)&?', address).group(1)
            vidlink = 'https://www.youtube.com/watch?v=' + vidid

        def download_video(vidlink, vidid, upload_dir):
            import youtube_dl
            import os

            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
                "outtmpl": os.path.join(upload_dir, vidid + ".%(ext)s")
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([vidlink])

        # start thread
        ydl_thread = threading.Thread(
            target=download_video,
            args=(vidlink, vidid, app.config['UPLOAD_FOLDER'])
        )
        print('Opening thread...')
        ydl_thread.start()
        print('Closing thread...')

        flash(
            'The video is downloading. Refresh the page later for new links.',
            'alert-success'
        )

    return render_template('index.html', videos=videos)


@app.route('/download/<video>')
def download(video=None):
    # scan upload folder for existing videos
    videos = [
        f for f in os.listdir(app.config['UPLOAD_FOLDER'])
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f)) and len(f) <= 15
    ]

    video_names = [f[:-4] for f in videos]

    vid_dict = dict(zip(video_names, videos))

    if video:
        try:
            return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']),
                                       vid_dict[video],
                                       as_attachment=True)
        except Exception:
            flash('File not found!', 'alert-danger')

    return render_template('index.html', videos=video_names)


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
    # app.run(host='localhost', debug=True)
