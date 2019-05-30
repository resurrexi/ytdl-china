from __future__ import unicode_literals
import os
import threading
import re
import time
import sqlite3

from flask import Flask, render_template, request, flash, send_from_directory
from flask import redirect

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


def get_videos():
    conn = sqlite3.connect(os.path.join(app.config['UPLOAD_FOLDER'],
                                        'db.sqlite'))
    cur = conn.cursor()
    cur.execute('''
    SELECT vidid
        ,filename
        ,title
        ,createts
    FROM videos
    ORDER BY createts DESC
    ''')
    videos = cur.fetchall()
    cur.close()
    conn.close()
    return videos


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


@app.before_request
def before_request():
    if not request.is_secure and app.env != "development":
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)


@app.route('/', methods=['GET', 'POST'])
def index():
    # get video list
    videos = get_videos()

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
        if vidid in [v[0] for v in videos]:  # 0 index refers to vidid
            flash(
                'The video already exists. Please check the links below.',
                'alert-info'
            )
            return render_template('index.html', videos=videos)

        def download_video(vidlink, vidid, upload_dir, logger, hook):
            import youtube_dl
            import os
            import sqlite3
            import json

            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(upload_dir, vidid + '.%(ext)s'),
                'writeinfojson': True,
                'logger': logger,
                'progress_hooks': [hook],
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([vidlink])

            # fetch video info with json file
            ctime = os.stat(os.path.join(
                upload_dir, '{}.info.json'.format(vidid)
            )).st_ctime
            with open(os.path.join(
                upload_dir, '{}.info.json'.format(vidid)
            )) as file:
                info = json.load(file)

            # write to database
            conn = sqlite3.connect(os.path.join(upload_dir, 'db.sqlite'))
            cur = conn.cursor()
            cur.execute('''
            INSERT INTO videos
            VALUES
            (?, ?, ?, ?)
            ''', (vidid, info['_filename'], info['title'], ctime))
            conn.commit()
            cur.close()
            conn.close()

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
    # get video list
    videos = get_videos()

    vid_dict = {}
    for v in videos:
        vid_dict.update({v[0]: v[1]})  # idx 0 is vidid, idx 1 is filename

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
