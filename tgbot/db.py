import sqlite3

conn = sqlite3.connect("casino.db", check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA temp_store=MEMORY;")
cursor = conn.cursor()

# ускорение
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 100,
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        games INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0
    )
    """)
    conn.commit()

def user_exists(user_id):
    cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

def create_user(user_id, username):
    cursor.execute(
        "INSERT INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "balance": row[2],
        "level": row[3],
        "xp": row[4],
        "games": row[5],
        "wins": row[6],
        "losses": row[7],
    }

def update_user(user):
    cursor.execute("""
    UPDATE users SET
        username=?,
        balance=?,
        level=?,
        xp=?,
        games=?,
        wins=?,
        losses=?
    WHERE user_id=?
    """, (
        user["username"],
        user["balance"],
        user["level"],
        user["xp"],
        user["games"],
        user["wins"],
        user["losses"],
        user["user_id"]
    ))
    conn.commit()