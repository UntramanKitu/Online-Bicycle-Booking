import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
for t in tables:
    try:
        cur.execute(f"DROP TABLE IF EXISTS {t[0]};")
    except Exception as e:
        print(f"Could not drop {t[0]}: {e}")
conn.commit()
print("All tables dropped.")
