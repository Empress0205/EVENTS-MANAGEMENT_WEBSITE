import os
import sqlite3

def init_db():
    db_path = 'instance/event.db'
    os.makedirs('instance', exist_ok=True)  # Ensure the 'instance' directory exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create `users` table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # Create `events` table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        time TEXT NOT NULL,
        photo TEXT,
        location TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    

    conn.commit()
    conn.close()

# Call this once at startup
init_db()
