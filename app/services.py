# File: app/services.py (Updated - Add this function)
import requests
import re
import json
import time
import logging
import random
from flask import current_app
from typing import Optional, List, Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# --- YouTube Service ---

def extract_video_id(url: str) -> Optional[str]:
    """Extracts the YouTube video ID from various URL formats."""
    patterns = [
        r"watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"embed/([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_comments(video_id: str, max_results: int = 50) -> List[str]:
    """Fetches top-level comments from a YouTube video."""
    api_key = current_app.config['YOUTUBE_API_KEY']
    if not api_key:
        logger.error("YouTube API Key is not configured.")
        raise Exception("Service is not configured to connect to YouTube.")
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=max_results,
            order='relevance',
            textFormat='plainText'
        )
        response = request.execute()
        return [item['snippet']['topLevelComment']['snippet']['textDisplay'] for item in response.get('items', []) if len(item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', '').strip()) > 10]
    except HttpError as e:
        err_details = json.loads(e.content).get('error', {}).get('errors', [{}])[0]
        reason = err_details.get('reason', 'unknown')
        logger.error(f"YouTube API error ({e.resp.status}): {reason}")
        if reason == 'commentsDisabled':
            raise Exception("Comments are disabled for this video.")
        raise Exception("YouTube API error. Check key and quotas.")
    except Exception as e:
        logger.error(f"Unexpected error fetching YouTube comments: {e}")
        raise

def get_youtube_channel_videos(channel_id: str, max_results: int = 50) -> List[Dict]:
    """
    Fetches videos from a YouTube channel with comprehensive metadata.
    Returns a list of video dictionaries with all relevant information.
    """
    api_key = current_app.config['YOUTUBE_API_KEY']
    if not api_key:
        logger.error("YouTube API Key is not configured.")
        raise Exception("YouTube API service is not configured.")
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # First, get the channel's uploads playlist ID
        channel_request = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get('items'):
            logger.error(f"Channel not found: {channel_id}")
            return []
        
        # Get the uploads playlist ID
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from the uploads playlist
        playlist_request = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=min(max_results, 50)  # YouTube API limit
        )
        playlist_response = playlist_request.execute()
        
        # Extract video IDs
        video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response.get('items', [])]
        
        if not video_ids:
            logger.info(f"No videos found for channel {channel_id}")
            return []
        
        # Get detailed video information
        videos_request = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids)
        )
        videos_response = videos_request.execute()
        
        videos = []
        for video_data in videos_response.get('items', []):
            snippet = video_data.get('snippet', {})
            statistics = video_data.get('statistics', {})
            content_details = video_data.get('contentDetails', {})
            
            # Get the best thumbnail
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = ""
            for quality in ['maxres', 'high', 'medium', 'default']:
                if quality in thumbnails:
                    thumbnail_url = thumbnails[quality].get('url', '')
                    break
            
            # Parse duration (PT4M13S -> 4:13)
            duration = content_details.get('duration', '')
            duration_seconds = parse_youtube_duration(duration)
            
            video_info = {
                'video_id': video_data.get('id'),
                'title': snippet.get('title', 'Untitled Video'),
                'description': snippet.get('description', '')[:200],  # Truncate description
                'thumbnail_url': thumbnail_url,
                'published_at': snippet.get('publishedAt', ''),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'duration': duration,
                'duration_seconds': duration_seconds,
                'tags': snippet.get('tags', [])[:5],  # Limit to first 5 tags
                'category_id': snippet.get('categoryId'),
                'default_language': snippet.get('defaultLanguage'),
                'has_captions': content_details.get('caption') == 'true'
            }
            videos.append(video_info)
        
        # Sort by published date (newest first)
        videos.sort(key=lambda x: x['published_at'], reverse=True)
        
        logger.info(f"Successfully fetched {len(videos)} videos for channel {channel_id}")
        return videos
        
    except HttpError as e:
        error_details = json.loads(e.content).get('error', {})
        error_reason = error_details.get('errors', [{}])[0].get('reason', 'unknown')
        logger.error(f"YouTube API HTTP error ({e.resp.status}) fetching videos for {channel_id}: {error_reason}")
        
        if e.resp.status == 403:
            raise Exception("YouTube API quota exceeded or access denied")
        elif e.resp.status == 404:
            raise Exception("Channel not found or has no public videos")
        else:
            raise Exception(f"YouTube API error: {error_reason}")
            
    except Exception as e:
        logger.error(f"Unexpected error fetching videos for channel {channel_id}: {e}")
        raise Exception(f"Failed to fetch channel videos: {str(e)}")

def parse_youtube_duration(duration: str) -> int:
    """
    Parse YouTube duration format (PT4M13S) to seconds.
    Returns 0 if parsing fails.
    """
    if not duration:
        return 0
    
    try:
        # Remove PT prefix
        duration = duration.replace('PT', '')
        
        # Extract hours, minutes, seconds
        hours = 0
        minutes = 0
        seconds = 0
        
        if 'H' in duration:
            hours_match = re.search(r'(\d+)H', duration)
            if hours_match:
                hours = int(hours_match.group(1))
        
        if 'M' in duration:
            minutes_match = re.search(r'(\d+)M', duration)
            if minutes_match:
                minutes = int(minutes_match.group(1))
        
        if 'S' in duration:
            seconds_match = re.search(r'(\d+)S', duration)
            if seconds_match:
                seconds = int(seconds_match.group(1))
        
        return hours * 3600 + minutes * 60 + seconds
        
    except Exception as e:
        logger.warning(f"Could not parse duration '{duration}': {e}")
        return 0

def get_video_captions(video_id: str) -> Optional[str]:
    """
    Attempts to fetch captions/transcript for a YouTube video.
    Note: This requires OAuth for most videos due to YouTube's policies.
    Returns None if captions are not available or accessible.
    """
    api_key = current_app.config['YOUTUBE_API_KEY']
    if not api_key:
        return None
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # List available captions
        captions_request = youtube.captions().list(
            part='snippet',
            videoId=video_id
        )
        captions_response = captions_request.execute()
        
        # Look for English captions
        for caption in captions_response.get('items', []):
            if caption['snippet']['language'] in ['en', 'en-US', 'en-GB']:
                caption_id = caption['id']
                
                # Try to download the caption
                # Note: This often requires OAuth authentication
                download_request = youtube.captions().download(
                    id=caption_id,
                    tfmt='srt'  # SubRip format
                )
                caption_content = download_request.execute()
                return caption_content
        
        return None
        
    except HttpError as e:
        # Expected for most videos due to access restrictions
        logger.debug(f"Could not fetch captions for video {video_id}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error fetching captions for video {video_id}: {e}")
        return None

def get_youtube_channel_details(channel_url: str) -> Optional[Dict]:
    """
    Fetches comprehensive channel details from a given YouTube channel URL.
    Handles multiple URL formats and provides better error handling.
    """
    api_key = current_app.config['YOUTUBE_API_KEY']
    if not api_key:
        logger.error("YouTube API Key is not configured.")
        raise Exception("YouTube API service is not configured.")
    
    # Parse different YouTube URL formats
    params = {}
    channel_id = None
    username = None
    
    # Clean up the URL
    channel_url = channel_url.strip().replace('www.', '')
    
    # Pattern 1: youtube.com/channel/CHANNEL_ID
    if match := re.search(r"youtube\.com/channel/([a-zA-Z0-9_-]+)", channel_url):
        channel_id = match.group(1)
        params['id'] = channel_id
        
    # Pattern 2: youtube.com/@USERNAME (new format)
    elif match := re.search(r"youtube\.com/@([a-zA-Z0-9_.-]+)", channel_url):
        username = match.group(1)
        params['forHandle'] = '@' + username
        
    # Pattern 3: youtube.com/c/USERNAME (legacy custom URL)
    elif match := re.search(r"youtube\.com/c/([a-zA-Z0-9_.-]+)", channel_url):
        username = match.group(1)
        params['forUsername'] = username
        
    # Pattern 4: youtube.com/user/USERNAME (very old format)
    elif match := re.search(r"youtube\.com/user/([a-zA-Z0-9_.-]+)", channel_url):
        username = match.group(1)
        params['forUsername'] = username
        
    # Pattern 5: Just the username/handle (try to detect format)
    elif not channel_url.startswith('http'):
        if channel_url.startswith('@'):
            params['forHandle'] = channel_url
        else:
            params['forUsername'] = channel_url
    
    if not params:
        logger.error(f"Could not parse channel identifier from URL: {channel_url}")
        return None

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Try the parsed parameters first
        request = youtube.channels().list(part="snippet,statistics", **params)
        response = request.execute()
        
        # If no results and we used username/handle, try alternative approaches
        if not response.get("items") and username:
            # Try different parameter combinations
            alternative_params = [
                {'forHandle': f'@{username}'},
                {'forUsername': username},
                {'forHandle': username}
            ]
            
            for alt_params in alternative_params:
                if alt_params != params:  # Don't repeat the same query
                    try:
                        request = youtube.channels().list(part="snippet,statistics", **alt_params)
                        response = request.execute()
                        if response.get("items"):
                            break
                    except:
                        continue
        
        if not response.get("items"):
            logger.warning(f"No channel found for URL: {channel_url}")
            return None
            
        channel_data = response["items"][0]
        stats = channel_data.get("statistics", {})
        snippet = channel_data.get("snippet", {})
        
        # Get the best available thumbnail
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = ""
        for quality in ['high', 'medium', 'default']:
            if quality in thumbnails:
                thumbnail_url = thumbnails[quality].get("url", "")
                break
        
        return {
            'channel_id': channel_data.get("id"),
            'title': snippet.get("title", "Unknown Channel"),
            'description': snippet.get("description", "")[:500],  # Limit description length
            'thumbnail': thumbnail_url,
            'subscriber_count': int(stats.get("subscriberCount", 0)),
            'video_count': int(stats.get("videoCount", 0)),
            'view_count': int(stats.get("viewCount", 0)),
            'channel_verified': snippet.get("customUrl") is not None,  # Rough verification check
            'created_at': snippet.get("publishedAt", "")
        }
        
    except HttpError as e:
        error_details = json.loads(e.content).get('error', {})
        error_reason = error_details.get('errors', [{}])[0].get('reason', 'unknown')
        logger.error(f"YouTube API HTTP error ({e.resp.status}) for {channel_url}: {error_reason}")
        
        if e.resp.status == 403:
            raise Exception("YouTube API quota exceeded or access denied")
        elif e.resp.status == 404:
            return None  # Channel not found
        else:
            raise Exception(f"YouTube API error: {error_reason}")
            
    except Exception as e:
        logger.error(f"Unexpected error fetching channel details for {channel_url}: {e}")
        raise Exception(f"Failed to fetch channel data: {str(e)}")

def extract_channel_id_from_url(url: str) -> Optional[str]:
    """
    Extract channel ID from various YouTube URL formats.
    This is a helper function for URL parsing.
    """
    patterns = [
        r"youtube\.com/channel/([a-zA-Z0-9_-]+)",
        r"youtube\.com/@([a-zA-Z0-9_.-]+)",
        r"youtube\.com/c/([a-zA-Z0-9_.-]+)",
        r"youtube\.com/user/([a-zA-Z0-9_.-]+)"
    ]
    
    for pattern in patterns:
        if match := re.search(pattern, url):
            return match.group(1)
    
    return None

def validate_youtube_url(url: str) -> bool:
    """
    Validate if a URL looks like a valid YouTube channel URL.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic YouTube domain check
    if not ('youtube.com' in url.lower() or 'youtu.be' in url.lower()):
        return False
    
    # Check for channel indicators
    channel_indicators = ['/@', '/channel/', '/c/', '/user/']
    return any(indicator in url for indicator in channel_indicators)

# --- IBM NLU Service ---
class IBMNaturalLanguageUnderstanding:
    
    def _make_request(self, text_to_analyze: str, features: Dict) -> Optional[Dict]:
        api_key = current_app.config.get('IBM_NLU_API_KEY')
        service_url = current_app.config.get('IBM_NLU_URL')
        version = current_app.config.get('IBM_NLU_VERSION', '2022-04-07')
        
        if not all([api_key, service_url, version]):
            logger.error("IBM NLU is not configured.")
            return None

        url = f"{service_url}/v1/analyze?version={version}"
        headers = {"Content-Type": "application/json"}
        auth = ('apikey', api_key)
        data = {"text": text_to_analyze, "features": features}

        try:
            response = requests.post(url, headers=headers, auth=auth, json=data, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"IBM NLU API call error: {e}")
            return None

    def analyze_sentiment_emotion(self, text_to_analyze: str) -> Optional[Dict]:
        """Analyzes text for sentiment and emotion."""
        features = {"sentiment": {}, "emotion": {}}
        return self._make_request(text_to_analyze, features)
        
    def analyze_themes(self, text_to_analyze: str) -> Optional[Dict]:
        """Analyzes text for concepts and entities to identify themes."""
        features = {
            "concepts": {"limit": 3},
            "entities": {"limit": 3, "sentiment": False, "emotion": False}
        }
        return self._make_request(text_to_analyze, features)

# --- IBM Watsonx AI Service ---
class IBMWatsonxAI:
    def __init__(self):
        self.is_available = False
        logger.warning("IBM watsonx.ai connection is OFF for demo purposes, using fallback mode.")

    def generate_content(self, prompt: str, model_id: str, max_tokens: int = 500) -> str:
        return self._generate_fallback_script(prompt)

    def _generate_fallback_script(self, prompt: str) -> str:
        topic = "your topic"
        if match := re.search(r'topic of "(.*?)"', prompt, re.IGNORECASE):
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
(Upbeat music fades in)"""
        
        return script

# Instantiate services
nlu_service = IBMNaturalLanguageUnderstanding()
watsonx_ai = IBMWatsonxAI()