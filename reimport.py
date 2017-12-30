import sqlite3
from datetime import datetime as dt
import baropi as b
from concurrent.futures import ProcessPoolExecutor, wait
b.init_db()

db = sqlite3.connect(b.config.__dbfile__)
cursor = db.cursor()
cursor.execute('''SELECT * FROM clima_samples''')
all_rows = cursor.fetchall()
print("%s rows of data" % len(all_rows))


def migrate_row(row):
    s = b.ClimateSample(
        (row[2], row[1])
    )
    s.timestamp = dt.strptime(row[3], "%Y-%m-%d %H:%M:%S")
    b.db_session.add(s)


executor = ProcessPoolExecutor(8)
futures = [executor.submit(migrate_row, row) for row in all_rows]
wait(futures)
b.db_session.commit()
