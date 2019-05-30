import sqlite3
import os

filepath = os.path.dirname(os.path.abspath(__file__))

conn = sqlite3.connect(os.path.join(filepath, 'uploads', 'db.sqlite'))
cur = conn.cursor()

cur.execute('''
CREATE TABLE videos (
    vidid TEXT UNIQUE,
    filename TEXT UNIQUE,
    title TEXT,
    createts REAL
)
''')

conn.commit()
cur.close()
conn.close()
