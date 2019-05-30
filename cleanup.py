import os
import time
import sqlite3

filepath = os.path.dirname(os.path.abspath(__file__))
upload_path = os.path.join(filepath, 'uploads')

# grab database records
conn = sqlite3.connect(os.path.join(upload_path, 'db.sqlite'))
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

# iterate through records and remove videos older than 24hr
now = time.time()

for v in videos:
    if now - v[3] > 86400:  # idx 3 is createts
        os.remove(os.path.join(upload_path, v[1]))  # idx 1 is filename
        cur.execute('DELETE FROM videos WHERE vidid = ?', (v[0],))
        conn.commit()

cur.close()
conn.close()
