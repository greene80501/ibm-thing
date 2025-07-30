# File: app/utils.py
import random
import re
import datetime
from datetime import timedelta, date

# --- Context Processor ---
def utility_processor():
    """Makes utility functions available in all templates."""
    def get_type_icon(t):
        return {
            'sentiment': 'fas fa-chart-pie', 'theme_cluster': 'fas fa-project-diagram',
            'competitor': 'fas fa-tachometer-alt', 'script': 'fas fa-edit',
            'calendar': 'fas fa-calendar-alt'
        }.get(t, 'fas fa-chart-bar')

    def get_type_color(t):
        return {
            'sentiment': 'bg-blue-600/20', 'theme_cluster': 'bg-purple-600/20',
            'competitor': 'bg-orange-600/20', 'script': 'bg-red-600/20',
            'calendar': 'bg-emerald-600/20'
        }.get(t, 'bg-slate-600/20')

    return dict(getTypeIcon=get_type_icon, getTypeColor=get_type_color)


# --- Mock Data and Helper Functions ---
def get_channel_info_from_url(url):
    """Generates mock channel info for demo fallback."""
    if 'youtube.com' in url or 'youtu.be' in url:
        return {
            'channel_id': f'mock-channel-id-{random.randint(100, 999)}',
            'title': f'Demo Channel - {random.choice(["Gaming", "Cooking", "Tech"])}',
            'description': 'This is a mock channel generated for the demo.',
            'thumbnail': 'https://yt3.googleusercontent.com/ytc/AIdro_k-g0_G0Xp-4_f5_Y8Z_g0_G0Xp-4_f5_Y8=s176-c-k-c0x00ffffff-no-rj',
            'subscriber_count': random.randint(5000, 150000), 'video_count': random.randint(50, 300),
            'view_count': random.randint(500000, 10000000)
        }
    return None

# generate_mock_competitors has been removed as it is now obsolete.

def generate_mock_videos(count=12):
    videos = []
    for i in range(count):
        views = random.randint(1000, 100000)
        videos.append({
            "video_id": f"mock-video-{i}", "title": f"My Awesome Video Vol. {i+1}",
            "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            "published_at": (datetime.datetime.now() - timedelta(days=random.randint(5, 365))).isoformat(),
            "view_count": views, "comment_count": int(views * random.uniform(0.001, 0.005)),
            "has_transcript": random.choice([True, True, False])
        })
    return sorted(videos, key=lambda x: x['published_at'], reverse=True)

def generate_smart_calendar_content(content_goals, platforms, posting_frequency, content_duration):
    freq_map = {'daily': 7, 'frequent': 5, 'regular': 3, 'weekly': 1}
    posts_per_week = freq_map.get(posting_frequency, 5)
    total_posts = posts_per_week * content_duration
    topics = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', content_goals) or ["New Content"]
    content_types = {'youtube': ['Video', 'Short'], 'instagram': ['Post', 'Reel'], 'tiktok': ['Video'], 'twitter': ['Tweet', 'Thread']}
    optimal_times = {'youtube': '6:00 PM', 'instagram': '11:00 AM', 'tiktok': '9:00 PM', 'twitter': '9:00 AM'}
    
    calendar_items = []
    today = date.today()
    for i in range(total_posts):
        platform = random.choice(platforms)
        post_date = today + timedelta(days=int((i / posts_per_week) * 7))
        calendar_items.append({
            'date': post_date.strftime('%Y-%m-%d'), 'day': post_date.strftime('%A'),
            'time': optimal_times.get(platform, '12:00 PM'), 'title': f"{random.choice(topics)} Post",
            'platform': platform, 'content_type': random.choice(content_types.get(platform, ['Post'])),
            'engagement_score': random.randint(65, 95)
        })
    
    metrics = {
        'total_posts': total_posts, 'optimal_time_coverage': total_posts,
        'content_types_used': len(set(i['content_type'] for i in calendar_items)),
        'avg_engagement': sum(item['engagement_score'] for item in calendar_items) / total_posts if total_posts > 0 else 0
    }
    return {'calendar_items': sorted(calendar_items, key=lambda x: x['date']), 'metrics': metrics}

def generate_ai_recommendations(calendar_result, content_goals, platforms):
    return ["Excellent cross-platform strategy.", "The 'Tutorial' theme is well-suited for YouTube.", "AI has optimized post times for peak engagement."]

def generate_performance_predictions(metrics, platforms):
    return [
        {'metric': 'Expected Reach', 'value': f"+{int(len(platforms) * 15)}%", 'color': 'emerald', 'icon': 'fas fa-users'},
        {'metric': 'Engagement Rate', 'value': f"~{metrics.get('avg_engagement', 75):.1f}%", 'color': 'blue', 'icon': 'fas fa-heart'}
    ]