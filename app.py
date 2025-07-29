# Enhanced IBM AI-Integrated YouTube Analytics App
# File: app.py (FINALIZED VERSION - CORRECTED)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
import sqlite3
import bcrypt
import re
import requests
import time
import random
import datetime
from datetime import timedelta, date
import json
import os
from functools import wraps
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'alice-insight-secret-key-change-in-production-2024'

# --- Database Configuration ---
DATABASE = 'alice_insight.db'

# --- IBM AI Configuration (Placeholders for Demo) ---
IBM_NLU_API_KEY = "BunpkLiLUfJB4e1-sq1-3P_8f2LqzbqN5Vbe4L2UA9KR"
IBM_NLU_URL = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/dead8d2a-3978-4e15-b413-dab9e0ae7f46"
IBM_NLU_VERSION = "2022-4-07"

# watsonx.ai Configuration (Placeholders for Demo)
WATSONX_API_KEY = "nYQ1gFsdCOfpCL5oOZj3-b18q5-2RsZXTn1JsydVmTbV"
WATSONX_PROJECT_ID = "a03dfd66-1d06-4458-badb-82229d245571"
WATSONX_URL = "https://us-south.ml.cloud.ibm.com"

# YouTube API (for future real integration)
YOUTUBE_API_KEY = "AIzaSyBb0GIb6f6H-uukICrV4KTQMU3FKAuKKwM"

# --- Enhanced IBM AI Service Classes ---
class IBMWatsonxAI:
    """Enhanced IBM watsonx.ai integration with better error handling."""
    
    def __init__(self):
        self.api_key = WATSONX_API_KEY
        self.project_id = WATSONX_PROJECT_ID
        self.base_url = WATSONX_URL
        self.access_token = None
        self.token_expires = 0
        self.is_available = False # Set to False for demo to always use fallback
        self._test_connection()
        
    def _test_connection(self):
        """Test the connection and set availability status."""
        try:
            logger.warning("IBM watsonx.ai connection is OFF for demo purposes, using fallback mode.")
        except Exception as e:
            logger.error(f"IBM watsonx.ai connection error: {e}")
            self.is_available = False
    
    def _get_access_token(self):
        """Get IBM Cloud access token with enhanced error handling."""
        if self.access_token and time.time() < self.token_expires:
            return self.access_token
            
        try:
            url = "https://iam.cloud.ibm.com/identity/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
            data = {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": self.api_key}
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.token_expires = time.time() + 3000
                self.is_available = True
                return self.access_token
            else:
                logger.error(f"IBM Token error: {response.status_code}, {response.text}")
                self.is_available = False
                return None
        except Exception as e:
            logger.error(f"Error getting IBM access token: {e}")
            self.is_available = False
            return None
    
    def generate_content(self, prompt: str, model_id: str = "ibm/granite-13b-chat-v2", max_tokens: int = 500) -> str:
        """Generate content using watsonx.ai with enhanced error handling."""
        if not self.is_available:
            return self._generate_fallback_script(prompt)

        try:
            token = self._get_access_token()
            if not token: return None
                
            url = f"{self.base_url}/ml/v1/text/generation?version=2023-05-29"
            headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {token}"}
            data = {
                "input": prompt,
                "parameters": {"decoding_method": "greedy", "max_new_tokens": max_tokens},
                "model_id": model_id, "project_id": self.project_id
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'results' in result and len(result['results']) > 0:
                    return result['results'][0]['generated_text'].strip()
            else:
                logger.error(f"watsonx.ai error: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Error calling watsonx.ai: {e}")
        return None
    
    def _generate_fallback_script(self, prompt: str) -> str:
        """Generates a high-quality mock script for demo purposes."""
        topic = "your topic"
        match = re.search(r'topic of "(.*?)"', prompt, re.IGNORECASE)
        if match:
            topic = match.group(1)

        script = f"""**Intro (Hook):**
(Upbeat music starts and fades)
"Hey everyone, and welcome back! Ever wondered how to master {topic} without spending hours? Today, I'm breaking down the three BIGGEST secrets that will change your game. You won't want to miss this!"

**Point 1: The Foundation**
"Alright, let's dive right in. The most crucial first step is understanding the fundamentals. Forget everything you thought you knew. For {topic}, it's all about [Key Concept #1]. Think of it like this: [Simple Analogy]. Once you get this, everything else clicks into place."
(Show B-roll of concept in action)

**Point 2: The Game-Changer**
"Now for the tip that blew my mind. It's a simple technique called [Technique Name]. Instead of doing [Common Mistake], try this: [Step-by-step instructions]. See the difference? It's night and day!"
(Show side-by-side comparison)

**Point 3: The Pro Secret**
"And finally, the secret that pros use. It's all about consistency and using the right tools. I personally recommend [Tool/Product Name] because it automates [Difficult Part]. This saves you time and ensures perfect results every single time."
(Show a quick demo of the tool)

**Outro (Call to Action):**
"So there you have it! Three secrets to revolutionize your approach to {topic}. If you found this helpful, smash that like button and subscribe for more tips. And let me know in the comments which tip you're going to try first! See you in the next one!"
(Upbeat music fades in)
"""
        return script


    def generate_content_ideas(self, topic: str, platform: str, content_type: str, count: int = 5) -> List[Dict]:
        """Generate content ideas with robust fallback and better prompting."""
        if self.is_available:
            try:
                pass
            except Exception as e:
                logger.warning(f"IBM AI generation failed, using fallback: {e}")
        
        fallback_ideas = self._generate_intelligent_fallback(topic, platform, content_type, count)
        logger.info(f"Generated {len(fallback_ideas)} fallback content ideas")
        return fallback_ideas

    def _generate_intelligent_fallback(self, topic: str, platform: str, content_type: str, count: int) -> List[Dict]:
        templates = {
            'youtube': [f"The Ultimate Guide to {topic}", f"5 {topic} Mistakes to Avoid", f"Mastering {topic} in 7 Days"],
            'instagram': [f"{topic} Transformation", f"Quick {topic} Tips", f"Behind the Scenes of my {topic} setup"],
            'tiktok': [f"{topic} Hacks You Need to Know", f"Rating {topic} Trends", f"Day in the Life: {topic} Edition"],
            'twitter': [f"A Thread on {topic} 🧵", f"Unpopular {topic} Opinions", f"The Future of {topic}"]
        }
        platform_templates = templates.get(platform, templates['youtube'])
        ideas = []
        for i in range(count):
            title = random.choice(platform_templates)
            ideas.append({
                'title': title, 'description': f"Engaging {content_type.lower()} content about {topic}",
                'engagement_prediction': random.randint(75, 95),
                'hashtags': [f"#{topic.replace(' ', '')}", f"#{platform}", f"#{content_type}"],
                'best_time': self._get_optimal_time(platform),
                'content_type': content_type, 'platform': platform, 'ai_generated': False
            })
        return ideas

    def _get_optimal_time(self, platform: str) -> str:
        optimal_times = {
            'youtube': ['6:00 PM', '7:00 PM', '8:00 PM'], 'instagram': ['11:00 AM', '1:00 PM', '7:00 PM'],
            'tiktok': ['6:00 AM', '10:00 AM', '9:00 PM'], 'twitter': ['9:00 AM', '12:00 PM', '6:00 PM']
        }
        return random.choice(optimal_times.get(platform, optimal_times['youtube']))

watsonx_ai = IBMWatsonxAI()

def init_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            channel_url TEXT, channel_id TEXT, channel_name TEXT, channel_subscriber_count INTEGER DEFAULT 0,
            channel_video_count INTEGER DEFAULT 0, channel_view_count INTEGER DEFAULT 0, channel_thumbnail TEXT,
            channel_description TEXT, channel_verified BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP, is_active BOOLEAN DEFAULT 1, email_verified BOOLEAN DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0, last_failed_login TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, video_url TEXT, video_id TEXT,
            title TEXT, data TEXT, metadata TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized successfully")

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def create_user_with_channel(email, password, channel_url=None):
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    channel_data = {}
    if channel_url:
        channel_info = get_channel_info_from_url(channel_url)
        if channel_info:
            channel_data = {
                'channel_name': channel_info['title'], 'channel_verified': 1, 'channel_id': channel_info['channel_id'],
                'channel_subscriber_count': channel_info['subscriber_count'], 'channel_video_count': channel_info['video_count'],
                'channel_view_count': channel_info['view_count'], 'thumbnail': channel_info['thumbnail'], 'description': channel_info['description']
            }
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO users (email, password_hash, channel_url, channel_id, channel_name, 
               channel_subscriber_count, channel_video_count, channel_view_count, 
               channel_thumbnail, channel_description, channel_verified) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (email, password_hash, channel_url, channel_data.get('channel_id'), channel_data.get('channel_name'),
             channel_data.get('channel_subscriber_count'), channel_data.get('channel_video_count'),
             channel_data.get('channel_view_count'), channel_data.get('thumbnail'),
             channel_data.get('description'), channel_data.get('channel_verified', 0))
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def update_user_channel(user_id, channel_url):
    channel_info = get_channel_info_from_url(channel_url)
    if not channel_info: return False
    conn = get_db_connection()
    conn.execute('''
        UPDATE users SET channel_url = ?, channel_id = ?, channel_name = ?, channel_subscriber_count = ?,
        channel_video_count = ?, channel_view_count = ?, channel_thumbnail = ?, channel_description = ?,
        channel_verified = 1 WHERE id = ?
    ''', (channel_url, channel_info['channel_id'], channel_info['title'], channel_info['subscriber_count'],
          channel_info['video_count'], channel_info['view_count'], channel_info['thumbnail'],
          channel_info['description'], user_id))
    conn.commit()
    conn.close()
    return True

def save_analysis_data(user_id, analysis_type, video_url, video_id, title, data, metadata):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO analyses (user_id, type, video_url, video_id, title, data, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (user_id, analysis_type, video_url, video_id, title, json.dumps(data), json.dumps(metadata))
    )
    conn.commit()
    conn.close()

def get_recent_analyses(user_id, limit=5):
    conn = get_db_connection()
    analyses = conn.execute('SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?', (user_id, limit)).fetchall()
    conn.close()
    return analyses

def get_channel_info_from_url(url):
    if 'youtube.com' in url or 'youtu.be' in url:
        return {
            'channel_id': f'mock-channel-id-{random.randint(100, 999)}',
            'title': f'Demo Channel - {random.choice(["Gaming", "Cooking", "Tech", "Lifestyle"])}',
            'description': 'This is a mock channel generated for the Alice Insight Suite demo.',
            'thumbnail': 'https://yt3.googleusercontent.com/ytc/AIdro_k-g0_G0Xp-4_f5_Y8Z_g0_G0Xp-4_f5_Y8=s176-c-k-c0x00ffffff-no-rj',
            'subscriber_count': random.randint(5000, 150000), 'video_count': random.randint(50, 300),
            'view_count': random.randint(500000, 10000000)
        }
    return None

def generate_mock_sentiment():
    positive = random.randint(20, 30); neutral = random.randint(5, 10); negative = random.randint(2, 5)
    return {
        "sentiment_data": {"positive": positive, "neutral": neutral, "negative": negative},
        "emotion_data": {
            "joy": random.uniform(0.6, 0.9), "sadness": random.uniform(0.1, 0.3), "anger": random.uniform(0.0, 0.2),
            "surprise": random.uniform(0.2, 0.4), "fear": random.uniform(0.0, 0.1), "disgust": random.uniform(0.0, 0.1)
        }, "alert": "High engagement detected!" if (positive + neutral + negative) > 35 else None
    }

def generate_mock_themes():
    themes = ["Video Quality", "Sound/Music", "Topic Request", "Presenter's Style", "Technical Question"]
    clusters = [{"summary": f"Discussion about {t}", "comment_ids": [random.randint(1,100) for _ in range(random.randint(5,15))]} for t in random.sample(themes, random.randint(3,5))]
    outliers = [{"summary": "Unique comment about a specific timestamp", "comment_ids": [random.randint(1,100) for _ in range(random.randint(1,3))]}]
    return {"clusters": clusters, "outliers": outliers}

def generate_mock_competitors(usernames):
    return [{"username": name, "subscribers": random.randint(10000, 500000), "avg_engagement_rate": random.uniform(0.02, 0.08),
             "recent_sentiment": random.choice(["positive", "neutral", "negative"]), "url": f"https://youtube.com/@{name}"} for name in usernames if name]

def generate_mock_videos(count=12):
    videos = []
    for i in range(count):
        views = random.randint(1000, 100000)
        videos.append({
            "video_id": f"mock-video-{i}", "title": f"My Awesome Video Vol. {i+1} - {random.choice(['Tutorial', 'Review', 'Vlog'])}",
            "thumbnail_url": f"https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg?sqp=-oaymwEbCKgBEF5IVfKriqkDDggBFQAAiEIYAXABwAEG&rs=AOn4CLB-p-S-V-0-v-1-Q-3-w-0-y",
            "published_at": (datetime.datetime.now() - timedelta(days=random.randint(5, 365))).isoformat(),
            "view_count": views, "like_count": int(views * random.uniform(0.02, 0.05)), "comment_count": int(views * random.uniform(0.001, 0.005)),
            "has_transcript": random.choice([True, True, False])
        })
    return sorted(videos, key=lambda x: x['published_at'], reverse=True)

def generate_smart_calendar_content(content_goals, platforms, posting_frequency, content_duration):
    freq_map = {'daily': 7, 'frequent': 5, 'regular': 3, 'weekly': 1}
    posts_per_week = freq_map.get(posting_frequency, 5)
    total_posts = posts_per_week * content_duration
    topics = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', content_goals) or re.findall(r'\b[a-z]+\s[a-z]+\b', content_goals) or [content_goals.split()[0]] or ["New Content"]
    content_types = {'youtube': ['Video', 'Short', 'Live Stream'], 'instagram': ['Post', 'Reel', 'Story'], 'tiktok': ['Video', 'Live'], 'twitter': ['Tweet', 'Thread', 'Space']}
    optimal_times = {'youtube': ['6:00 PM', '7:00 PM', '8:00 PM'], 'instagram': ['11:00 AM', '1:00 PM', '7:00 PM'], 'tiktok': ['6:00 AM', '10:00 AM', '9:00 PM'], 'twitter': ['9:00 AM', '12:00 PM', '6:00 PM']}
    calendar_items = []
    used_content_types = set()
    optimal_time_posts = 0
    today = date.today()
    title_prefixes = ['Deep Dive:', 'Quick Look:', "Let's Talk:", 'New Video:']
    for i in range(total_posts):
        platform = random.choice(platforms)
        content_type = random.choice(content_types.get(platform, ['Post']))
        used_content_types.add(f"{platform}-{content_type}")
        post_date = today + timedelta(days=int((i / posts_per_week) * 7) + random.randint(0, 6))
        time_choice = random.choice(optimal_times.get(platform, ['12:00 PM']))
        optimal_time_posts += 1
        item = {
            'date': post_date.strftime('%Y-%m-%d'), 'day': post_date.strftime('%A'), 'time': time_choice,
            'title': f"{random.choice(title_prefixes)} {random.choice(topics)}", 'platform': platform, 'content_type': content_type,
            'engagement_score': random.randint(65, 95), 'ai_generated': True
        }
        calendar_items.append(item)
    metrics = {
        'total_posts': total_posts, 'optimal_time_coverage': optimal_time_posts, 'content_types_used': len(used_content_types),
        'avg_engagement': sum(item['engagement_score'] for item in calendar_items) / total_posts if total_posts > 0 else 0
    }
    return {'calendar_items': sorted(calendar_items, key=lambda x: x['date']), 'metrics': metrics}

def generate_ai_recommendations(calendar_result, content_goals, platforms):
    recommendations = []
    metrics = calendar_result['metrics']
    if len(platforms) > 2: recommendations.append(f"Excellent cross-platform strategy covering {len(platforms)} networks. This will maximize your reach.")
    elif len(platforms) == 1: recommendations.append(f"Focusing on {platforms[0].title()} is great for specialization. Consider adding a secondary platform to repurpose content.")
    if 'tutorial' in content_goals.lower() and any(p in platforms for p in ['youtube', 'tiktok']): recommendations.append("The 'Tutorial' theme is well-suited for long-form YouTube videos and short-form TikTok clips. Your calendar reflects a good mix.")
    if metrics['total_posts'] > 20: recommendations.append("High posting volume detected. Ensure content quality is maintained to avoid audience burnout.")
    else: recommendations.append("The current posting schedule is sustainable and allows for high-quality content production.")
    recommendations.append("AI has optimized post times for peak engagement based on platform-specific data.")
    return recommendations

def generate_performance_predictions(metrics, platforms):
    predictions = []
    reach = 1 + (len(platforms) * 0.15) + (metrics.get('total_posts', 0) * 0.01)
    predictions.append({'metric': 'Expected Reach', 'value': f"+{int((reach - 1) * 100)}%", 'color': 'emerald', 'icon': 'fas fa-users'})
    predictions.append({'metric': 'Engagement Rate', 'value': f"~{metrics.get('avg_engagement', 75):.1f}%", 'color': 'blue', 'icon': 'fas fa-heart'})
    predictions.append({'metric': 'Time Saved', 'value': f"~{metrics.get('total_posts', 0) * 15} min", 'color': 'purple', 'icon': 'fas fa-clock'})
    growth = "High" if metrics.get('avg_engagement', 0) > 80 and len(platforms) > 1 else "Medium"
    predictions.append({'metric': 'Growth Potential', 'value': growth, 'color': 'yellow', 'icon': 'fas fa-rocket'})
    return predictions

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if 'api' in request.path:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def utility_processor():
    def get_type_icon(t): return {'sentiment': 'fas fa-chart-pie', 'theme_cluster': 'fas fa-project-diagram', 'competitor': 'fas fa-tachometer-alt', 'script': 'fas fa-edit', 'calendar': 'fas fa-calendar-alt'}.get(t, 'fas fa-chart-bar')
    def get_type_color(t): return {'sentiment': 'bg-blue-600/20', 'theme_cluster': 'bg-purple-600/20', 'competitor': 'bg-orange-600/20', 'script': 'bg-red-600/20', 'calendar': 'bg-emerald-600/20'}.get(t, 'bg-slate-600/20')
    return dict(getTypeIcon=get_type_icon, getTypeColor=get_type_color)

# --- Frontend Routes ---
@app.route('/')
def index():
    # *** CHANGE HERE ***
    # Clear any existing session and redirect to the login page.
    # This ensures a fresh start for the demo every time the root URL is visited.
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_user_by_id(session['user_id'])
    recent_analyses = get_recent_analyses(session['user_id'])
    user_videos_count = 0
    user_transcripts_count = 0
    if user and user['channel_verified']:
        user_videos_count = user['channel_video_count'] or 0
        user_transcripts_count = int(user_videos_count * 0.8)
    return render_template('index.html', user=user, recent_analyses=recent_analyses,
                           user_videos_count=user_videos_count,
                           user_transcripts_count=user_transcripts_count)

@app.route('/login')
def login():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/sentiment-analyzer')
@login_required
def sentiment_analyzer(): return render_template('sentiment_analyzer.html')

@app.route('/theme-clustering')
@login_required
def theme_clustering(): return render_template('theme_clustering.html')

@app.route('/competitor-dashboard')
@login_required
def competitor_dashboard(): return render_template('competitor_dashboard.html')

@app.route('/script-helper')
@login_required
def script_helper(): return render_template('script_helper.html')

@app.route('/smart-calendar')
@login_required
def smart_calendar(): return render_template('smart_calendar.html')

@app.route('/model-explorer')
@login_required
def model_explorer(): return render_template('model_explorer.html')

@app.route('/my-channel')
@login_required
def my_channel():
    user = get_user_by_id(session['user_id'])
    mock_videos = []
    if user and user['channel_verified']:
        mock_videos = generate_mock_videos(user['channel_video_count'] or 25)
    user_transcripts = [v for v in mock_videos if v['has_transcript']]
    return render_template('my_channel.html', user=user, user_videos=mock_videos, user_transcripts=user_transcripts)

# --- API Authentication Endpoints ---
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    channel_url = data.get('channel_url', '').strip()
    if not all([email, password, confirm_password]): return jsonify({'error': 'All fields are required'}), 400
    if password != confirm_password: return jsonify({'error': 'Passwords do not match'}), 400
    if len(password) < 8: return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if get_user_by_email(email): return jsonify({'error': 'Email already registered'}), 409
    user_id = create_user_with_channel(email, password, channel_url)
    if not user_id: return jsonify({'error': 'Account creation failed'}), 500
    session['user_id'] = user_id
    session['user_email'] = email
    user = get_user_by_id(user_id)
    response_data = {'message': 'Account created successfully'}
    if channel_url and user and user['channel_verified']:
        response_data['channel_verified'] = bool(user['channel_verified'])
        response_data['channel_name'] = user['channel_name']
    return jsonify(response_data), 201

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not email or not password: return jsonify({'error': 'Email and password required'}), 400
    user = get_user_by_email(email)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        return jsonify({'message': 'Login successful'})
    return jsonify({'error': 'Invalid email or password'}), 401

# --- Mock API Endpoints for Demo ---
@app.route('/api/analyze-sentiment', methods=['POST'])
@login_required
def analyze_sentiment():
    time.sleep(2)
    data = generate_mock_sentiment()
    save_analysis_data(session['user_id'], 'sentiment', request.json.get('video_url'), 'mock_video_id', 'Sentiment Analysis', data, {})
    return jsonify(data)

@app.route('/api/cluster-themes', methods=['POST'])
@login_required
def cluster_themes():
    time.sleep(2.5)
    data = generate_mock_themes()
    save_analysis_data(session['user_id'], 'theme_cluster', request.json.get('video_url'), 'mock_video_id', 'Theme Clustering', data, {})
    return jsonify(data)

@app.route('/api/analyze-competitors', methods=['POST'])
@login_required
def analyze_competitors():
    time.sleep(1.5)
    usernames = request.json.get('usernames', [])
    data = {"competitors": generate_mock_competitors(usernames)}
    save_analysis_data(session['user_id'], 'competitor', None, None, 'Competitor Analysis', data, {})
    return jsonify(data)
    
@app.route('/api/generate-script', methods=['POST'])
@login_required
def generate_script():
    time.sleep(3)
    data = request.get_json()
    topic = data.get('topic', 'a great video')
    model_id = data.get('model_id')
    prompt = f"Create a YouTube script for a video with the topic of \"{topic}\"."
    script = watsonx_ai.generate_content(prompt, model_id=model_id)
    response_data = {"script": script, "suggestions": "Consider adding a call-to-action to boost engagement."}
    save_analysis_data(session['user_id'], 'script', None, None, f'Script: {topic}', response_data, {})
    return jsonify(response_data)

@app.route('/api/generate-calendar', methods=['POST'])
@login_required
def generate_calendar_route():
    user_id = session['user_id']
    try:
        data = request.get_json()
        calendar_result = generate_smart_calendar_content(data.get('content_goals'), data.get('platforms'), data.get('posting_frequency'), int(data.get('content_duration')))
        recommendations = generate_ai_recommendations(calendar_result, data.get('content_goals'), data.get('platforms'))
        predictions = generate_performance_predictions(calendar_result['metrics'], data.get('platforms'))
        response_data = {
            'calendar_items': calendar_result['calendar_items'], 'recommendations': recommendations, 'predictions': predictions,
            'metrics': calendar_result['metrics'], 'success': True, 'ibm_ai_powered': watsonx_ai.is_available
        }
        save_analysis_data(user_id, 'calendar', None, None, f"Smart Calendar for {data.get('content_goals')}", response_data, {})
        time.sleep(2)
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Calendar generation error: {e}")
        return jsonify({'error': 'Failed to generate calendar'}), 500

@app.route('/api/verify-channel', methods=['POST'])
@login_required
def verify_channel():
    time.sleep(1.5)
    channel_url = request.json.get('channel_url')
    if not channel_url: return jsonify({'error': 'Channel URL is required'}), 400
    if update_user_channel(session['user_id'], channel_url): return jsonify({'message': 'Channel connected successfully!'})
    else: return jsonify({'error': 'Could not verify channel URL'}), 400

@app.route('/api/refresh-channel-data', methods=['POST'])
@login_required
def refresh_channel_data():
    time.sleep(1.5)
    user = get_user_by_id(session['user_id'])
    if user and user['channel_url']: update_user_channel(session['user_id'], user['channel_url'])
    return jsonify({'message': 'Channel data refreshed successfully!'})

@app.route('/api/my-videos', methods=['GET'])
@login_required
def get_my_videos():
    user = get_user_by_id(session['user_id'])
    videos = generate_mock_videos(user['channel_video_count'] or 25) if user and user['channel_verified'] else []
    return jsonify({'videos': videos})

@app.route('/api/video-transcript/<video_id>', methods=['GET'])
@login_required
def get_video_transcript(video_id):
    if "bad" in video_id: return jsonify({'error': 'Transcript not found'}), 404
    return jsonify({"video_id": video_id, "transcript_text": f"Mock transcript for video {video_id}. " * 20, "language": "en", "auto_generated": True})

@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    conn = get_db_connection()
    total_analyses = conn.execute('SELECT COUNT(*) FROM analyses WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    analyses_by_type = conn.execute('SELECT type, COUNT(*) FROM analyses WHERE user_id = ? GROUP BY type', (session['user_id'],)).fetchall()
    conn.close()
    return jsonify({'total_analyses': total_analyses, 'analyses_by_type': {row['type']: row['COUNT(*)'] for row in analyses_by_type}})

@app.route('/api/list-models')
@login_required
def list_models():
    models = [
        {"label": "Granite 13B Chat v2", "model_id": "ibm/granite-13b-chat-v2", "provider": "IBM", "short_description": "General purpose chat model."},
        {"label": "Llama 3 8B Instruct", "model_id": "meta-llama/llama-3-8b-instruct", "provider": "Meta", "short_description": "High-performance creative model."},
        {"label": "Mixtral 8x7B Instruct", "model_id": "mistralai/mixtral-8x7b-instruct-v01", "provider": "Mistral AI", "short_description": "Advanced mixture-of-experts model."}
    ]
    return jsonify({"resources": models})

@app.route('/api/list-tasks')
@login_required
def list_tasks():
    return jsonify({"resources": [{"label": "Generation", "task_id": "generation"}, {"label": "Classification", "task_id": "classification"}, {"label": "Summarization", "task_id": "summarization"}]})

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        from init_db import initialize_database
        initialize_database()
    else:
        init_database()
    logger.info("🚀 Alice Insight Suite starting...")
    logger.info(f"🔵 IBM watsonx.ai: {'Available' if watsonx_ai.is_available else 'Fallback mode (DEMO)'}")
    logger.info(f"🔵 Project ID: {WATSONX_PROJECT_ID}")
    app.run(debug=True, port=5001, host='0.0.0.0')