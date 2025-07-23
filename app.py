# Enhanced YouTube Analytics App with Fixed Authentication
# File: app.py (REPLACE the existing app.py)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import bcrypt
import re
import requests
import time
import random
import datetime
import json
import os
from functools import wraps

# ------------------------------------------------------------------
# --- Alice Insight Suite - Fixed Authentication Version
# ------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = 'alice-insight-secret-key-change-in-production-2024'  # Change this in production!

# --- Database Configuration ---
DATABASE = 'alice_insight.db'

# --- API Configuration ---
YOUTUBE_API_KEY = "AIzaSyBb0GIb6f6H-uukICrV4KTQMU3FKAuKKwM"
IBM_NLU_API_KEY = "BunpkLiLUfJB4e1-sq1-3P_8f2LqzbqN5Vbe4L2UA9KR"
IBM_NLU_URL = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/dead8d2a-3978-4e15-b413-dab9e0ae7f46"
IBM_NLU_VERSION = "2022-04-07"
WATSONX_API_KEY = "nYQ1gFsdCOfpCL5oOZj3-b18q5-2RsZXTn1JsydVmTbV"
WATSONX_PROJECT_ID = "a03dfd66-1d06-4458-badb-82229d245571"
WATSONX_URL = "https://us-south.ml.cloud.ibm.com"

# --- Enhanced Database Initialization ---
def init_database():
    """Initialize the SQLite database with required tables including channel data."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Enhanced Users table with channel information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            channel_url TEXT,
            channel_id TEXT,
            channel_name TEXT,
            channel_subscriber_count INTEGER DEFAULT 0,
            channel_video_count INTEGER DEFAULT 0,
            channel_view_count INTEGER DEFAULT 0,
            channel_thumbnail TEXT,
            channel_description TEXT,
            channel_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # User's channel videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            published_at TEXT,
            thumbnail_url TEXT,
            duration TEXT,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            tags TEXT,  -- JSON array of tags
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, video_id)
        )
    ''')
    
    # Video transcripts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_id TEXT NOT NULL,
            transcript_text TEXT,
            language TEXT DEFAULT 'en',
            auto_generated BOOLEAN DEFAULT 1,
            transcript_data TEXT,  -- JSON with timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, video_id)
        )
    ''')
    
    # Data table (keep existing structure)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            data_type TEXT NOT NULL,
            video_url TEXT,
            video_id TEXT,
            title TEXT,
            analysis_data TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # API usage tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            usage_count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully with channel integration!")

# --- Enhanced Database Helper Functions ---
def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    """Get user by email with channel info."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def create_user_with_channel(email, password, channel_url=None):
    """Create a new user with optional channel information."""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # If channel URL provided, get channel info
    channel_data = {}
    if channel_url:
        channel_info = get_channel_info_from_url(channel_url)
        if channel_info:
            channel_data = {
                'channel_url': channel_url,
                'channel_id': channel_info.get('channel_id'),
                'channel_name': channel_info.get('title'),
                'channel_subscriber_count': channel_info.get('subscriber_count', 0),
                'channel_video_count': channel_info.get('video_count', 0),
                'channel_view_count': channel_info.get('view_count', 0),
                'channel_thumbnail': channel_info.get('thumbnail'),
                'channel_description': channel_info.get('description', ''),
                'channel_verified': 1
            }
    
    conn = get_db_connection()
    try:
        # Insert user with channel data
        if channel_data:
            cursor = conn.execute(
                '''INSERT INTO users (email, password_hash, channel_url, channel_id, channel_name, 
                   channel_subscriber_count, channel_video_count, channel_view_count, 
                   channel_thumbnail, channel_description, channel_verified) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (email, password_hash, channel_data.get('channel_url'), 
                 channel_data.get('channel_id'), channel_data.get('channel_name'),
                 channel_data.get('channel_subscriber_count'), channel_data.get('channel_video_count'),
                 channel_data.get('channel_view_count'), channel_data.get('channel_thumbnail'),
                 channel_data.get('channel_description'), channel_data.get('channel_verified'))
            )
        else:
            cursor = conn.execute(
                'INSERT INTO users (email, password_hash) VALUES (?, ?)',
                (email, password_hash)
            )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def save_analysis_data(user_id, data_type, video_url, video_id, title, analysis_data, metadata=None):
    """Save analysis data to the database."""
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO data (user_id, data_type, video_url, video_id, title, analysis_data, metadata) 
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (user_id, data_type, video_url, video_id, title, json.dumps(analysis_data), 
         json.dumps(metadata) if metadata else None)
    )
    conn.commit()
    conn.close()

def get_user_data(user_id, data_type=None, limit=50):
    """Get user's analysis data."""
    conn = get_db_connection()
    if data_type:
        data = conn.execute(
            'SELECT * FROM data WHERE user_id = ? AND data_type = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, data_type, limit)
        ).fetchall()
    else:
        data = conn.execute(
            'SELECT * FROM data WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()
    conn.close()
    return data

# --- Mock YouTube Channel Helper Functions (since API may not work) ---
def get_channel_info_from_url(url):
    """Mock channel information extraction - replace with real API when available."""
    # Mock data for demonstration
    if 'youtube.com' in url or 'youtu.be' in url:
        return {
            'channel_id': 'mock-channel-id-123',
            'title': 'Test YouTube Channel',
            'description': 'This is a test channel for demonstration purposes.',
            'thumbnail': 'https://via.placeholder.com/88x88/3b82f6/ffffff?text=YT',
            'subscriber_count': 1250,
            'video_count': 25,
            'view_count': 125000
        }
    return None

# --- Authentication Decorator ---
def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def get_video_id_from_url(url):
    """Extracts the YouTube video ID from various URL formats."""
    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    return video_id_match.group(0) if video_id_match else None

def get_youtube_comments(video_id, max_results=50):
    """Mock YouTube comments - replace with real API when available."""
    # Mock comments for demonstration
    mock_comments = [
        {"id": "1", "text": "Great video! Very informative and helpful."},
        {"id": "2", "text": "This is amazing content, thank you for sharing!"},
        {"id": "3", "text": "I love this approach, will definitely try it."},
        {"id": "4", "text": "Could you make a follow-up video on this topic?"},
        {"id": "5", "text": "Excellent explanation, very clear and detailed."},
        {"id": "6", "text": "This video helped me so much, thank you!"},
        {"id": "7", "text": "Really good quality content, keep it up!"},
        {"id": "8", "text": "I disagree with some points but overall good video."},
        {"id": "9", "text": "Can you explain more about the technical aspects?"},
        {"id": "10", "text": "This is exactly what I was looking for!"}
    ]
    return mock_comments[:max_results]

# --- Calendar generation functions ---
def generate_calendar_content(content_goals, platforms, posting_frequency, duration_weeks):
    """Generate smart calendar content using AI and optimization algorithms."""
    optimal_times = {
        'youtube': ['6:00 PM', '8:00 PM', '9:00 PM'],
        'instagram': ['11:00 AM', '1:00 PM', '5:00 PM', '7:00 PM'],
        'tiktok': ['6:00 AM', '10:00 AM', '7:00 PM', '9:00 PM'],
        'twitter': ['9:00 AM', '12:00 PM', '3:00 PM', '6:00 PM']
    }
    
    best_days = {
        'youtube': ['Tuesday', 'Wednesday', 'Thursday', 'Saturday'],
        'instagram': ['Monday', 'Tuesday', 'Thursday', 'Friday'],
        'tiktok': ['Tuesday', 'Thursday', 'Friday', 'Saturday'],
        'twitter': ['Monday', 'Wednesday', 'Friday']
    }
    
    content_types = [
        'Tutorial', 'Behind-the-scenes', 'Tips & Tricks', 'Q&A', 'Product Review',
        'Educational', 'Entertainment', 'Trending Topic', 'User-generated Content',
        'Live Session', 'Story Time', 'How-to Guide', 'Industry News', 'Personal Update'
    ]
    
    posts_per_week = {
        'daily': 7, 'frequent': 5, 'regular': 3, 'weekly': 1
    }
    
    total_posts = posts_per_week.get(posting_frequency, 3) * duration_weeks
    calendar_items = []
    
    for week in range(duration_weeks):
        week_posts = posts_per_week.get(posting_frequency, 3)
        
        for post_num in range(week_posts):
            platform = platforms[post_num % len(platforms)] if platforms else 'youtube'
            available_days = best_days.get(platform, best_days['youtube'])
            day = available_days[post_num % len(available_days)]
            available_times = optimal_times.get(platform, optimal_times['youtube'])
            time_slot = available_times[post_num % len(available_times)]
            
            content_type = random.choice(content_types)
            topics = content_goals.split(',') if ',' in content_goals else [content_goals]
            topic = random.choice(topics).strip()
            
            title = f"{content_type}: {topic}"
            if len(title) > 50:
                title = title[:47] + "..."
            
            start_date = datetime.date.today() + datetime.timedelta(weeks=week)
            days_ahead = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(day)
            post_date = start_date + datetime.timedelta(days=days_ahead)
            
            calendar_items.append({
                'title': title,
                'content_type': content_type,
                'platform': platform,
                'day': day,
                'time': time_slot,
                'date': post_date.strftime('%Y-%m-%d'),
                'week': week + 1,
                'engagement_score': random.randint(70, 95)
            })
    
    return calendar_items

# ------------------------------------------------------------------
# --- Authentication Routes (FIXED)
# ------------------------------------------------------------------

@app.route('/login')
def login():
    """Display login page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')  # Fixed: removed 'auth/' prefix

@app.route('/register')
def register():
    """Display registration page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('register.html')  # Fixed: removed 'auth/' prefix

@app.route('/logout')
def logout():
    """Log out the user."""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Handle login API request."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user['is_active']:
        return jsonify({'error': 'Account is disabled'}), 401
    
    # Set up session
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    
    # Update last login
    conn = get_db_connection()
    conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Login successful', 'user': {'id': user['id'], 'email': user['email']}})

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Handle registration API request with channel integration."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    channel_url = data.get('channel_url', '').strip()
    
    # Validation
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    # Email format validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # YouTube channel URL validation (if provided)
    if channel_url:
        youtube_patterns = [
            r'youtube\.com/channel/',
            r'youtube\.com/c/',
            r'youtube\.com/@',
            r'youtube\.com/user/'
        ]
        if not any(re.search(pattern, channel_url) for pattern in youtube_patterns):
            return jsonify({'error': 'Invalid YouTube channel URL format'}), 400
    
    # Check if user already exists
    if get_user_by_email(email):
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create user with channel info
    user_id = create_user_with_channel(email, password, channel_url)
    if not user_id:
        return jsonify({'error': 'Failed to create account. Please try again.'}), 500
    
    # Set up session
    session['user_id'] = user_id
    session['user_email'] = email
    
    response_data = {
        'message': 'Account created successfully', 
        'user': {'id': user_id, 'email': email}
    }
    
    # Add channel verification status
    if channel_url:
        user = get_user_by_id(user_id)
        if user and user['channel_verified']:
            response_data['channel_verified'] = True
            response_data['channel_name'] = user['channel_name']
        else:
            response_data['channel_verified'] = False
            response_data['channel_error'] = 'Could not verify YouTube channel'
    
    return jsonify(response_data), 201

# ------------------------------------------------------------------
# --- Protected Page Rendering Routes
# ------------------------------------------------------------------

@app.route('/')
@login_required
def index():
    """Enhanced dashboard with channel info and recent analyses."""
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    recent_data = get_user_data(user_id, limit=10)
    
    # Get user's videos count
    conn = get_db_connection()
    user_videos_count = conn.execute(
        'SELECT COUNT(*) as count FROM user_videos WHERE user_id = ?', (user_id,)
    ).fetchone()['count']
    
    user_transcripts_count = conn.execute(
        'SELECT COUNT(*) as count FROM video_transcripts WHERE user_id = ?', (user_id,)
    ).fetchone()['count']
    conn.close()
    
    # Convert to list of dicts for template
    recent_analyses = []
    for item in recent_data:
        recent_analyses.append({
            'id': item['id'],
            'type': item['data_type'],
            'title': item['title'] or 'Analysis',
            'created_at': item['created_at'],
            'video_url': item['video_url']
        })
    
    return render_template('index.html', 
                         recent_analyses=recent_analyses,
                         user=user,
                         user_videos_count=user_videos_count,
                         user_transcripts_count=user_transcripts_count)

@app.route('/sentiment-analyzer')
@login_required
def sentiment_analyzer(): 
    return render_template('sentiment_analyzer.html')

@app.route('/theme-clustering')
@login_required
def theme_clustering(): 
    return render_template('theme_clustering.html')

@app.route('/competitor-dashboard')
@login_required
def competitor_dashboard(): 
    return render_template('competitor_dashboard.html')

@app.route('/script-helper')
@login_required
def script_helper(): 
    return render_template('script_helper.html')

@app.route('/smart-calendar')
@login_required
def smart_calendar(): 
    return render_template('smart_calendar.html')

@app.route('/my-channel')
@login_required
def my_channel():
    """User's channel dashboard."""
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    # Get user's videos and transcripts
    conn = get_db_connection()
    user_videos = conn.execute(
        'SELECT * FROM user_videos WHERE user_id = ? ORDER BY published_at DESC',
        (user_id,)
    ).fetchall()
    
    user_transcripts = conn.execute(
        'SELECT * FROM video_transcripts WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    conn.close()
    
    return render_template('my_channel.html', 
                         user=user, 
                         user_videos=user_videos,
                         user_transcripts=user_transcripts)

# ------------------------------------------------------------------
# --- API Endpoints
# ------------------------------------------------------------------

@app.route('/api/analyze-sentiment', methods=['POST'])
@login_required
def analyze_sentiment():
    """Analyze sentiment with mock data for demonstration."""
    user_id = session['user_id']
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({"error": "Video URL is required"}), 400
        
    video_id = get_video_id_from_url(video_url)
    if not video_id: 
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    # Get mock comments
    comments = get_youtube_comments(video_id, max_results=40)
    if not comments: 
        return jsonify({"error": "Could not fetch comments or no comments found."}), 404
    
    # Mock sentiment analysis
    sentiment_counts = {"positive": 6, "neutral": 2, "negative": 2}
    emotion_counts = {"joy": 4, "anger": 1, "sadness": 1, "surprise": 2, "disgust": 0}
    
    alert = ""
    if sentiment_counts['negative'] / len(comments) > 0.4:
        alert = "Alert: High spike in negative sentiment detected!"
    
    # Save analysis to database
    analysis_data = {
        'sentiment_data': sentiment_counts,
        'emotion_data': emotion_counts,
        'alert': alert,
        'total_comments': len(comments)
    }
    
    title = f"Sentiment Analysis - {video_id}"
    save_analysis_data(user_id, 'sentiment', video_url, video_id, title, analysis_data)
    
    return jsonify(analysis_data)

@app.route('/api/cluster-themes', methods=['POST'])
@login_required
def cluster_themes():
    """Mock theme clustering analysis."""
    user_id = session['user_id']
    
    data = request.get_json()
    video_url = data.get('video_url')
    video_id = get_video_id_from_url(video_url)
    
    # Mock clustering results
    mock_clusters = [
        {
            "summary": "Tutorial and Educational Content",
            "comment_ids": ["1", "2", "5", "6", "7"]
        },
        {
            "summary": "Positive Feedback and Appreciation",
            "comment_ids": ["2", "3", "6", "10"]
        }
    ]
    
    mock_outliers = [
        {
            "summary": "Technical Questions and Clarifications",
            "comment_ids": ["4", "9"]
        }
    ]
    
    # Save to database
    analysis_data = {'clusters': mock_clusters, 'outliers': mock_outliers}
    title = f"Theme Clustering - {video_id}"
    save_analysis_data(user_id, 'clustering', video_url, video_id, title, analysis_data)
    
    return jsonify(analysis_data)

@app.route('/api/generate-script', methods=['POST'])
@login_required
def generate_script():
    """Generate mock script content."""
    user_id = session['user_id']
    
    data = request.get_json()
    topic = data.get('topic', 'Content Creation')
    
    # Mock script generation
    mock_script = f"""
# {topic}

## Introduction
Welcome back to our channel! Today we're diving deep into {topic.lower()}, and I'm excited to share some incredible insights with you.

## Main Content
Let's start with the fundamentals. {topic} is crucial for success in today's digital landscape. Here are the key points we'll cover:

1. Understanding the basics
2. Advanced techniques that work
3. Common mistakes to avoid
4. Pro tips for better results

## Key Takeaways
The most important thing to remember about {topic.lower()} is that consistency beats perfection every time. 

## Call to Action
If you found this helpful, don't forget to like this video and subscribe for more content like this. What aspect of {topic.lower()} would you like me to cover next? Let me know in the comments below!

## Closing
Thanks for watching, and I'll see you in the next video!
    """.strip()
    
    # Save to database
    analysis_data = {'script': mock_script, 'topic': topic}
    title = f"Generated Script - {topic}"
    save_analysis_data(user_id, 'script', None, None, title, analysis_data)
    
    return jsonify({
        'script': mock_script,
        'suggestions': f'Consider adding more specific examples related to {topic.lower()} to make the content more engaging.'
    })

@app.route('/api/generate-calendar', methods=['POST'])
@login_required
def generate_calendar():
    """Generate content calendar."""
    user_id = session['user_id']
    
    data = request.get_json()
    content_goals = data.get('content_goals', 'General content')
    posting_frequency = data.get('posting_frequency', 'regular')
    content_duration = data.get('content_duration', 2)
    platforms = data.get('platforms', ['youtube'])
    
    # Generate calendar
    calendar_items = generate_calendar_content(content_goals, platforms, posting_frequency, content_duration)
    
    # Mock recommendations
    recommendations = [
        f"Based on your focus on '{content_goals}', consider creating evergreen content that provides long-term value.",
        "Schedule your most important content during peak engagement hours (6-8 PM).",
        "Mix educational and entertaining content for better audience retention."
    ]
    
    response_data = {
        'calendar_items': calendar_items,
        'recommendations': recommendations,
        'predicted_engagement': random.randint(75, 90)
    }
    
    # Save to database
    title = f"Content Calendar - {content_duration} weeks"
    save_analysis_data(user_id, 'calendar', None, None, title, response_data)
    
    return jsonify(response_data)

@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics."""
    user_id = session['user_id']
    
    conn = get_db_connection()
    
    # Get total analyses
    total_analyses = conn.execute(
        'SELECT COUNT(*) as count FROM data WHERE user_id = ?', (user_id,)
    ).fetchone()['count']
    
    # Get analyses by type
    analyses_by_type = {}
    for row in conn.execute('SELECT data_type, COUNT(*) as count FROM data WHERE user_id = ? GROUP BY data_type', (user_id,)):
        analyses_by_type[row['data_type']] = row['count']
    
    conn.close()
    
    return jsonify({
        'total_analyses': total_analyses,
        'analyses_by_type': analyses_by_type
    })

# ------------------------------------------------------------------
# --- Error Handlers
# ------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    if request.is_json:
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    if request.is_json:
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

# ------------------------------------------------------------------
# --- Main Execution
# ------------------------------------------------------------------

if __name__ == '__main__':
    # Ensure templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("📁 Created templates directory")
    
    # Ensure static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
        if not os.path.exists('static/js'):
            os.makedirs('static/js')
        print("📁 Created static directories")
    
    # Initialize database
    init_database()
    
    print("🚀 Alice Insight Suite starting with FIXED authentication...")
    print("✅ Database initialized successfully")
    print("🔐 Authentication system ready")
    print("📊 Mock data enabled for demonstration")
    print("")
    print("🌐 Visit http://localhost:5001/register to create an account")
    print("🔗 Visit http://localhost:5001/login to sign in")
    print("📝 Test credentials will be created during registration")
    print("")
    print("🐛 Debug mode: ON (disable in production)")
    
    app.run(debug=True, port=5001)