import sqlite3
import bcrypt
import json
import random

DATABASE = 'alice_insight.db'

def initialize_database():
    """
    Initializes a fresh database, dropping old tables if they exist.
    Also populates the DB with a demo user and mock analysis data.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Drop existing tables to ensure a clean slate
    print("Dropping old tables (if they exist)...")
    cursor.execute('DROP TABLE IF EXISTS analyses')
    cursor.execute('DROP TABLE IF EXISTS users')

    # --- Create Users Table ---
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

    # --- Create Analyses Table ---
    print("Creating 'analyses' table...")
    cursor.execute('''
        CREATE TABLE analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, video_url TEXT, video_id TEXT,
            title TEXT, data TEXT, metadata TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # --- Populate with a Demo User ---
    print("Creating a demo user...")
    email = 'demo@alice.io'
    password = 'password123' # Simple password for the demo
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Demo channel data
    channel_url = 'https://www.youtube.com/@demochannel'
    channel_id = 'mock-channel-id-123'
    channel_name = 'Alice Demo Channel'
    channel_thumbnail = 'https://yt3.googleusercontent.com/ytc/AIdro_k-g0_G0Xp-4_f5_Y8Z_g0_G0Xp-4_f5_Y8=s176-c-k-c0x00ffffff-no-rj'
    
    cursor.execute(
        '''INSERT INTO users (email, password_hash, channel_url, channel_id, channel_name, channel_subscriber_count, channel_video_count, channel_view_count, channel_thumbnail, channel_description, channel_verified)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (email, password_hash, channel_url, channel_id, channel_name, 125000, 152, 2500000, channel_thumbnail, 'A demo channel for Alice Insight.', 1)
    )
    user_id = cursor.lastrowid
    print(f"✅ Demo user created! Email: {email}, Password: {password}")
    
    # --- Populate with Mock Analysis Data ---
    print("Populating with mock analysis data...")
    mock_analyses = [
        ('sentiment', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ', 'Sentiment Analysis: Viral Hits', {'sentiment_data': {'positive': 35, 'neutral': 5, 'negative': 2}}, {}),
        ('theme_cluster', 'https://www.youtube.com/watch?v=3JZ_D3p_fpQ', '3JZ_D3p_fpQ', 'Theme Cluster: Tech Reviews', {'clusters': [{'summary': 'Camera Quality'}, {'summary': 'Battery Life'}]}, {}),
        ('script', None, None, 'Script: How to Bake a Cake', {'script': 'Start with flour and sugar...'}, {}),
        ('competitor', None, None, 'Competitor Analysis: Top 3 Rivals', {'competitors': [{'username': 'Rival Channel 1'}]}, {}),
        ('calendar', None, None, 'Smart Calendar: August Content', {'metrics': {'total_posts': 12}}, {}),
    ]
    
    for analysis in mock_analyses:
        cursor.execute(
            'INSERT INTO analyses (user_id, type, video_url, video_id, title, data, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (user_id, analysis[0], analysis[1], analysis[2], analysis[3], json.dumps(analysis[4]), json.dumps(analysis[5]))
        )
    print(f"✅ Added {len(mock_analyses)} mock analyses for the demo user.")
    
    conn.commit()
    conn.close()
    
    print("\nDatabase initialization complete. You can now run the main app.")

if __name__ == '__main__':
    initialize_database()