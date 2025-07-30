# File: init_db.py
import sqlite3
import bcrypt
import json
import random

DATABASE = 'alice_insight.db' # Define the database file name

def initialize_database():
    """
    Initializes a fresh database, dropping old tables if they exist.
    Also populates the DB with a demo user and mock analysis data.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Dropping old tables (if they exist)...")
    cursor.execute('DROP TABLE IF EXISTS analyses')
    cursor.execute('DROP TABLE IF EXISTS users')

    print("Creating 'users' table...")
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            channel_url TEXT, channel_id TEXT, channel_name TEXT, channel_subscriber_count INTEGER DEFAULT 0,
            channel_video_count INTEGER DEFAULT 0, channel_view_count INTEGER DEFAULT 0, channel_thumbnail TEXT,
            channel_description TEXT, channel_verified BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP, is_active BOOLEAN DEFAULT 1, email_verified BOOLEAN DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0, last_failed_login TIMESTAMP
        )
    ''')

    print("Creating 'analyses' table...")
    cursor.execute('''
        CREATE TABLE analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, video_url TEXT, video_id TEXT,
            title TEXT, data TEXT, metadata TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    print("Creating a demo user...")
    email = 'demo@alice.io'
    password = 'password123'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    cursor.execute(
        'INSERT INTO users (email, password_hash, channel_url, channel_verified) VALUES (?, ?, ?, ?)',
        (email, password_hash, 'https://www.youtube.com/@demochannel', 1)
    )
    user_id = cursor.lastrowid
    print(f"✅ Demo user created! Email: {email}, Password: {password}")
    
    print("Populating with mock analysis data...")
    mock_analyses = [
        ('sentiment', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ', 'Sentiment: Viral Hits', {}, {}),
        ('theme_cluster', 'https://www.youtube.com/watch?v=3JZ_D3p_fpQ', '3JZ_D3p_fpQ', 'Theme: Tech Reviews', {}, {}),
        ('script', None, None, 'Script: How to Bake', {}, {}),
    ]
    
    for analysis in mock_analyses:
        cursor.execute(
            'INSERT INTO analyses (user_id, type, video_url, video_id, title, data, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, analysis[0], analysis[1], analysis[2], analysis[3], json.dumps(analysis[4]), json.dumps(analysis[5]))
        )
    print(f"✅ Added {len(mock_analyses)} mock analyses for the demo user.")
    
    conn.commit()
    conn.close()
    
    print("\nDatabase initialization complete.")

if __name__ == '__main__':
    initialize_database()