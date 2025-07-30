# File: app/database.py (Updated)
import sqlite3
import bcrypt
import json
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    """Connect to the application's configured database."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Clear existing data and create new tables."""
    db = get_db()
    with current_app.open_resource('database.sql', mode='r') as f:
        db.cursor().executescript(f.read())

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Command-line function to initialize the database."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    # The init-db command can now be run with `flask init-db`
    # However, we will use our standalone `init_db.py` for demo purposes
    # which is more explicit.

# --- User Functions ---
def get_user_by_email(email):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,)).fetchone()
    return user

def get_user_by_id(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return user

def create_user_with_channel(email, password, channel_url=None, channel_data=None):
    db = get_db()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    channel_data = channel_data or {}
    try:
        cursor = db.cursor()
        cursor.execute(
            '''INSERT INTO users (email, password_hash, channel_url, channel_id, channel_name, 
               channel_subscriber_count, channel_video_count, channel_view_count, 
               channel_thumbnail, channel_description, channel_verified) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (email, password_hash, channel_url, 
             channel_data.get('channel_id'), 
             channel_data.get('title'),  # Note: 'title' maps to 'channel_name'
             channel_data.get('subscriber_count'), 
             channel_data.get('video_count'),
             channel_data.get('view_count'), 
             channel_data.get('thumbnail'),
             channel_data.get('description'), 
             bool(channel_data.get('channel_id')))  # Verified if we have a channel_id
        )
        user_id = cursor.lastrowid
        db.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None

def update_user_channel(user_id, channel_url, channel_info):
    """Updated to handle the proper field mapping from services.get_youtube_channel_details()"""
    db = get_db()
    db.execute('''
        UPDATE users SET 
            channel_url = ?, 
            channel_id = ?, 
            channel_name = ?, 
            channel_subscriber_count = ?,
            channel_video_count = ?, 
            channel_view_count = ?, 
            channel_thumbnail = ?, 
            channel_description = ?,
            channel_verified = 1 
        WHERE id = ?
    ''', (
        channel_url, 
        channel_info['channel_id'], 
        channel_info['title'],  # 'title' from API maps to 'channel_name' in DB
        channel_info['subscriber_count'],
        channel_info['video_count'], 
        channel_info['view_count'], 
        channel_info['thumbnail'],
        channel_info['description'], 
        user_id
    ))
    db.commit()

# --- Video Cache Functions (Optional - for performance) ---
def cache_user_videos(user_id, videos_data):
    """
    Cache video data to reduce API calls.
    This is optional but recommended for production use.
    """
    db = get_db()
    # Clear existing cached videos for this user
    db.execute('DELETE FROM cached_videos WHERE user_id = ?', (user_id,))
    
    # Insert new video data
    for video in videos_data:
        db.execute('''
            INSERT INTO cached_videos 
            (user_id, video_id, title, thumbnail_url, published_at, view_count, 
             like_count, comment_count, duration, has_captions, cached_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            user_id,
            video['video_id'],
            video['title'],
            video['thumbnail_url'],
            video['published_at'],
            video['view_count'],
            video.get('like_count', 0),
            video['comment_count'],
            video.get('duration', ''),
            video.get('has_captions', False)
        ))
    
    db.commit()

def get_cached_user_videos(user_id, max_age_hours=24):
    """
    Get cached videos if they're not too old.
    Returns None if cache is stale or empty.
    """
    db = get_db()
    videos = db.execute('''
        SELECT * FROM cached_videos 
        WHERE user_id = ? 
        AND datetime(cached_at, '+{} hours') > datetime('now')
        ORDER BY published_at DESC
    '''.format(max_age_hours), (user_id,)).fetchall()
    
    if videos:
        # Convert to list of dicts
        return [dict(video) for video in videos]
    return None

# --- Analysis Functions ---
def save_analysis_data(user_id, analysis_type, video_url, video_id, title, data, metadata):
    db = get_db()
    db.execute(
        'INSERT INTO analyses (user_id, type, video_url, video_id, title, data, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (user_id, analysis_type, video_url, video_id, title, json.dumps(data), json.dumps(metadata))
    )
    db.commit()

def get_recent_analyses(user_id, limit=5):
    db = get_db()
    analyses = db.execute('SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?', (user_id, limit)).fetchall()
    return analyses

def get_dashboard_stats(user_id):
    db = get_db()
    total_analyses = db.execute('SELECT COUNT(*) FROM analyses WHERE user_id = ?', (user_id,)).fetchone()[0]
    analyses_by_type = db.execute('SELECT type, COUNT(*) FROM analyses WHERE user_id = ? GROUP BY type', (user_id,)).fetchall()
    return {'total_analyses': total_analyses, 'analyses_by_type': {row['type']: row['COUNT(*)'] for row in analyses_by_type}}

def get_cached_analysis(user_id, video_id, analysis_type, max_age_hours=24):
    """
    Get a cached analysis if it's not too old.
    Returns the parsed data if found, otherwise None.
    """
    db = get_db()
    analysis = db.execute(f'''
        SELECT data, created_at FROM analyses
        WHERE user_id = ? 
        AND video_id = ? 
        AND type = ?
        AND datetime(created_at, '+{max_age_hours} hours') > datetime('now')
        ORDER BY created_at DESC
        LIMIT 1
    ''', (user_id, video_id, analysis_type)).fetchone()
    
    if analysis:
        # The 'data' column is stored as a JSON string, so we need to parse it.
        return json.loads(analysis['data'])
    return None