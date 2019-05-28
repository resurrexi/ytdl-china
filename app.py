from __future__ import unicode_literals
import os
import threading
import re
import time

from tinytag import TinyTag
from flask import Flask, render_template, request, flash, send_from_directory

# init vars for app
filepath = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(filepath, 'uploads')
app.config['STATIC_FOLDER'] = os.path.join(filepath, 'static')
app.config['TEMPLATE_FOLDER'] = os.path.join(filepath, 'templates')
app.secret_key = 'DDD'


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


def get_title(f):
    tag = TinyTag.get(f)
    return tag.title


def sorted_ls(path):
    return list(
        sorted(
            [
                (
                    f[:-4],
                    f,
                    get_title(os.path.join(path, f)),
                    os.stat(os.path.join(path, f)).st_ctime
                ) for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f)) and len(f) <= 15
            ],
            key=lambda f: os.stat(os.path.join(path, f[1])).st_ctime,
            reverse=True
        )
    )


@app.template_filter()
def tdiff(s, default='just now'):
    now = time.time()
    diff = int(now) - int(s)

    periods = (
        (diff // 86400, "day", "days"),
        (diff // 3600, "hour", "hours"),
        (diff // 60, "minute", "minutes"),
        (diff, "second", "seconds"),
    )

    for period, singular, plural in periods:
        if period > 0:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default


@app.route('/', methods=['GET', 'POST'])
def index():
    # scan upload folder for existing videos
    videos = sorted_ls(app.config['UPLOAD_FOLDER'])

    if request.method == 'POST':
        address = request.form['vidlink']

        if 'youtu.be' in address:
            idx = address.rfind('/')
            vidid = address[idx + 1:]
            vidlink = 'https://www.youtube.com/watch?v=' + vidid
        else:
            vidid = re.search(r'v=([a-zA-Z0-9\_\-]+)&?', address).group(1)
            vidlink = 'https://www.youtube.com/watch?v=' + vidid

        # check if video already exists in uploads folder
        if vidid in [v[0] for v in videos]:
            flash(
                'The video already exists. Please check the links below.',
                'alert-info'
            )
            return render_template('index.html', videos=videos)

        def download_video(vidlink, vidid, upload_dir, logger, hook):
            import youtube_dl
            import os

            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                'outtmpl': os.path.join(upload_dir, vidid + '.%(ext)s'),
                'postprocessors': [
                    {
                        'key': 'FFmpegMetadata'
                    },
                    {
                        'key': 'MetadataFromTitle',
                        'titleformat': '%(title)s'
                    }
                ],
                'logger': logger,
                'progress_hooks': [hook],
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([vidlink])

        # start thread
        ydl_thread = threading.Thread(
            target=download_video,
            args=(vidlink, vidid, app.config['UPLOAD_FOLDER'],
                  MyLogger(), my_hook)
        )
        ydl_thread.start()

        flash(
            'The video is downloading. Refresh the page later for new links.',
            'alert-primary'
        )

    return render_template('index.html', videos=videos)


@app.route('/download/<video>')
def download(video=None):
    # scan upload folder for existing videos
    videos = sorted_ls(app.config['UPLOAD_FOLDER'])

    vid_dict = {}
    for v in videos:
        vid_dict.update({v[0]: v[1]})

    if video:
        try:
            return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']),
                                       vid_dict[video],
                                       as_attachment=True)
        except Exception:
            flash('File not found!', 'alert-danger')

    return render_template('index.html', videos=videos)


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
    # app.run(host='0.0.0.0', debug=True)
