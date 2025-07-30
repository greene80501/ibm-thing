# File: app/routes.py (Updated)
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
from collections import defaultdict
import time
import random

from .auth import login_required
from . import database, services, utils

bp = Blueprint('routes', __name__)

# --- Page Routes ---
@bp.route('/')
def index():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    user = database.get_user_by_id(session['user_id'])
    recent_analyses = database.get_recent_analyses(session['user_id'])
    user_videos_count = user['channel_video_count'] if user and user['channel_video_count'] else 0
    user_transcripts_count = int(user_videos_count * 0.8)
    return render_template('index.html', user=user, recent_analyses=recent_analyses,
                           user_videos_count=user_videos_count, user_transcripts_count=user_transcripts_count)

@bp.route('/sentiment-analyzer')
@login_required
def sentiment_analyzer(): return render_template('sentiment_analyzer.html')

@bp.route('/theme-clustering')
@login_required
def theme_clustering(): return render_template('theme_clustering.html')

@bp.route('/competitor-dashboard')
@login_required
def competitor_dashboard(): return render_template('competitor_dashboard.html')

@bp.route('/script-helper')
@login_required
def script_helper(): return render_template('script_helper.html')

@bp.route('/smart-calendar')
@login_required
def smart_calendar(): return render_template('smart_calendar.html')

@bp.route('/model-explorer')
@login_required
def model_explorer(): return render_template('model_explorer.html')

@bp.route('/my-channel')
@login_required
def my_channel():
    user = database.get_user_by_id(session['user_id'])
    user_videos = []
    user_transcripts = []
    error_message = None
    
    if user and user['channel_verified'] and user['channel_id']:
        try:
            # Fetch real videos from YouTube API
            user_videos = services.get_youtube_channel_videos(user['channel_id'], max_results=50)
            
            # Filter videos that have captions (approximation for transcripts)
            user_transcripts = [v for v in user_videos if v.get('has_captions', False)]
            
            current_app.logger.info(f"Loaded {len(user_videos)} videos for user {user['email']}")
            
        except Exception as e:
            current_app.logger.error(f"Error fetching videos for user {user['email']}: {e}")
            error_message = str(e)
            # Fallback to empty list for now, or could use mock data
            user_videos = []
            user_transcripts = []
    
    return render_template('my_channel.html', 
                         user=user, 
                         user_videos=user_videos, 
                         user_transcripts=user_transcripts,
                         error_message=error_message)

# --- API Routes ---

@bp.route('/api/analyze-sentiment', methods=['POST'])
@login_required
def analyze_sentiment():
    video_url = request.json.get('video_url')
    if not video_url: return jsonify({'error': 'Video URL is required'}), 400
    video_id = services.extract_video_id(video_url)
    if not video_id: return jsonify({'error': 'Invalid YouTube URL provided'}), 400

    # --- Caching Logic ---
    cached_result = database.get_cached_analysis(session['user_id'], video_id, 'sentiment')
    if cached_result:
        current_app.logger.info(f"Returning cached sentiment analysis for video_id: {video_id}")
        cached_result['from_cache'] = True
        return jsonify(cached_result)

    try:
        comments = services.get_youtube_comments(video_id, max_results=50)
        if not comments: return jsonify({'error': 'No comments found or comments are disabled.'}), 404
        
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        emotion_totals = {'sadness': 0, 'joy': 0, 'fear': 0, 'disgust': 0, 'anger': 0}
        analyzed_count = 0

        for comment_text in comments:
            clean_comment = comment_text.strip()
            if len(clean_comment) < 10 or not any(c.isalnum() for c in clean_comment):
                continue

            analysis_result = services.nlu_service.analyze_sentiment_emotion(comment_text)
            if analysis_result:
                analyzed_count += 1
                sentiment_label = analysis_result.get('sentiment', {}).get('document', {}).get('label', 'neutral')
                sentiment_counts[sentiment_label] += 1
                emotions = analysis_result.get('emotion', {}).get('document', {}).get('emotion', {})
                for emotion, score in emotions.items():
                    if emotion in emotion_totals: emotion_totals[emotion] += score
        
        if analyzed_count == 0: return jsonify({'error': 'Could not analyze any of the comments found.'}), 500

        final_emotions = {e: t / analyzed_count for e, t in emotion_totals.items() if analyzed_count > 0}
        response_data = {"sentiment_data": sentiment_counts, "emotion_data": final_emotions}
        database.save_analysis_data(session['user_id'], 'sentiment', video_url, video_id, f'Real Sentiment: {video_id}', response_data, {'comments_analyzed': analyzed_count})
        response_data['from_cache'] = False
        return jsonify(response_data)
    except Exception as e:
        current_app.logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/api/cluster-themes', methods=['POST'])
@login_required
def cluster_themes():
    video_url = request.json.get('video_url')
    if not video_url: return jsonify({'error': 'Video URL is required'}), 400
    video_id = services.extract_video_id(video_url)
    if not video_id: return jsonify({'error': 'Invalid YouTube URL provided'}), 400

    # --- Caching Logic ---
    cached_result = database.get_cached_analysis(session['user_id'], video_id, 'theme_cluster')
    if cached_result:
        current_app.logger.info(f"Returning cached theme cluster for video_id: {video_id}")
        cached_result['from_cache'] = True
        return jsonify(cached_result)

    try:
        comments = services.get_youtube_comments(video_id, max_results=80)
        if not comments: return jsonify({'error': 'No comments found for this video.'}), 404
        
        themes_with_comments = defaultdict(list)
        
        for comment_text in comments:
            clean_comment = comment_text.strip()
            if len(clean_comment) < 15 or not any(c.isalnum() for c in clean_comment):
                continue
            time.sleep(0.05)
            analysis = services.nlu_service.analyze_themes(comment_text)
            if analysis:
                comment_themes = set()
                comment_themes.update([c['text'].title() for c in analysis.get('concepts', []) if c['relevance'] > 0.6])
                comment_themes.update([e['text'].title() for e in analysis.get('entities', []) if e['relevance'] > 0.5])
                for theme in comment_themes:
                    themes_with_comments[theme].append(comment_text)

        if not themes_with_comments: return jsonify({'error': 'Could not extract meaningful themes.'}), 500
            
        sorted_themes = sorted(themes_with_comments.items(), key=lambda item: len(item[1]), reverse=True)
        clusters, outliers = [], []
        
        for theme, associated_comments in sorted_themes:
            if len(associated_comments) > 1 and len(clusters) < 5:
                clusters.append({'summary': theme, 'comments': associated_comments})
            elif len(outliers) < 5:
                outliers.append({'summary': theme, 'comments': associated_comments})
        
        cluster_summaries = {c['summary'] for c in clusters}
        outliers = [o for o in outliers if o['summary'] not in cluster_summaries]

        response_data = {"clusters": clusters, "outliers": outliers[:3], "total_analyzed": len(comments)}
        database.save_analysis_data(session['user_id'], 'theme_cluster', video_url, video_id, f'Real Theme Cluster: {video_id}', response_data, {'comments_analyzed': len(comments)})
        response_data['from_cache'] = False
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"Theme clustering failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/api/verify-channel', methods=['POST'])
@login_required
def verify_channel():
    channel_url = request.json.get('channel_url')
    if not channel_url: return jsonify({'error': 'Channel URL is required'}), 400
    try:
        channel_info = services.get_youtube_channel_details(channel_url)
        if not channel_info: return jsonify({'error': 'Could not find a YouTube channel at that URL.'}), 404
        database.update_user_channel(session['user_id'], channel_url, channel_info)
        return jsonify({'message': f"Channel '{channel_info['title']}' connected successfully!", 'channel_info': channel_info})
    except Exception as e:
        return jsonify({'error': 'An internal error occurred.'}), 500

@bp.route('/api/refresh-channel-data', methods=['POST'])
@login_required
def refresh_channel_data():
    user = database.get_user_by_id(session['user_id'])
    if not user or not user['channel_url']: return jsonify({'error': 'No channel is connected.'}), 400
    try:
        channel_info = services.get_youtube_channel_details(user['channel_url'])
        if not channel_info: return jsonify({'error': 'Could not refresh data.'}), 404
        database.update_user_channel(session['user_id'], user['channel_url'], channel_info)
        return jsonify({'message': 'Channel data refreshed successfully!'})
    except Exception as e:
        return jsonify({'error': 'An internal error occurred.'}), 500

@bp.route('/api/analyze-competitors', methods=['POST'])
@login_required
def analyze_competitors():
    """Analyze competitor channels with enhanced error handling and data processing."""
    channel_urls = request.json.get('channel_urls', [])
    
    if not channel_urls:
        return jsonify({'error': 'Please provide at least one competitor channel URL.'}), 400

    competitor_data = []
    errors = []
    
    for url in channel_urls:
        try:
            # Add small delay to avoid rate limiting
            time.sleep(0.2)
            
            # Get channel details using the YouTube API
            details = services.get_youtube_channel_details(url)
            
            if details:
                # Calculate a more realistic engagement rate
                engagement_rate = 0.0
                if details['subscriber_count'] > 0 and details['view_count'] > 0:
                    # Simple engagement calculation: avg views per subscriber
                    # Adjusted to be more realistic (divide by 100 to get percentage-like values)
                    base_engagement = details['view_count'] / details['subscriber_count']
                    if details['video_count'] > 0:
                        base_engagement = base_engagement / details['video_count']
                    
                    # Normalize to a realistic percentage (0.5% to 15%)
                    engagement_rate = min(max(base_engagement / 50, 0.005), 0.15)

                # Generate mock sentiment (in a real app, this would analyze recent comments)
                sentiments = ['positive', 'neutral', 'negative']
                weights = [0.6, 0.3, 0.1]  # Bias towards positive
                recent_sentiment = random.choices(sentiments, weights=weights)[0]

                competitor_data.append({
                    "username": details['title'],
                    "subscribers": details['subscriber_count'],
                    "avg_engagement_rate": round(engagement_rate, 4),
                    "recent_sentiment": recent_sentiment,
                    "url": url,
                    "thumbnail": details.get('thumbnail', '')
                })
            else:
                errors.append(f"Could not find channel data for: {url}")
                
        except Exception as e:
            current_app.logger.error(f"Error analyzing competitor {url}: {str(e)}")
            errors.append(f"Error processing {url}: {str(e)}")
            
    if not competitor_data:
        return jsonify({
            'error': 'Could not retrieve data for any of the provided channels. Please check the URLs and try again.',
            'details': errors
        }), 404

    # Sort by subscriber count (descending)
    competitor_data.sort(key=lambda x: x['subscribers'], reverse=True)

    # Save analysis to database
    database.save_analysis_data(
        session['user_id'], 
        'competitor', 
        None, 
        None, 
        f'Competitor Analysis ({len(competitor_data)} channels)', 
        {"competitors": competitor_data}, 
        {"urls_analyzed": len(channel_urls), "errors": len(errors)}
    )
    
    response_data = {
        "competitors": competitor_data,
        "total_analyzed": len(competitor_data),
        "success": True
    }
    
    # Include errors only if there are any, but don't fail the request
    if errors:
        response_data["errors"] = errors[:5]  # Limit to first 5 errors
        response_data["warnings"] = f"{len(errors)} URLs could not be processed"
    
    return jsonify(response_data)

# --- UPDATED MY CHANNEL API ROUTES ---

@bp.route('/api/my-videos', methods=['GET'])
@login_required
def get_my_videos():
    """Get real videos from the user's connected YouTube channel."""
    user = database.get_user_by_id(session['user_id'])
    
    if not user or not user['channel_verified'] or not user['channel_id']:
        return jsonify({
            'error': 'No verified channel connected',
            'videos': []
        }), 400
    
    try:
        videos = services.get_youtube_channel_videos(user['channel_id'], max_results=50)
        
        return jsonify({
            'videos': videos,
            'total_count': len(videos),
            'channel_name': user['channel_name'],
            'success': True
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching videos for user {user['email']}: {e}")
        return jsonify({
            'error': f'Failed to fetch videos: {str(e)}',
            'videos': []
        }), 500

@bp.route('/api/video-transcript/<video_id>', methods=['GET'])
@login_required
def get_video_transcript(video_id):
    """
    Attempt to get transcript/captions for a specific video.
    Note: Most videos require OAuth for caption access.
    """
    try:
        # Try to get captions using the YouTube API
        transcript = services.get_video_captions(video_id)
        
        if transcript:
            return jsonify({
                "video_id": video_id,
                "transcript_text": transcript,
                "language": "en",
                "auto_generated": True,  # Most accessible captions are auto-generated
                "success": True
            })
        else:
            # Return a helpful message explaining why transcript might not be available
            return jsonify({
                'error': 'Transcript not available. This could be because: '
                         '1) Captions are disabled for this video, '
                         '2) The video owner has restricted caption access, '
                         '3) No captions exist for this video, or '
                         '4) Additional authentication is required.'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error fetching transcript for video {video_id}: {e}")
        return jsonify({
            'error': f'Failed to fetch transcript: {str(e)}'
        }), 500

@bp.route('/api/video-details/<video_id>', methods=['GET'])
@login_required
def get_video_details(video_id):
    """Get detailed information about a specific video."""
    user = database.get_user_by_id(session['user_id'])
    
    if not user or not user['channel_verified']:
        return jsonify({'error': 'No verified channel connected'}), 400
    
    try:
        # Get all channel videos (or implement caching to avoid repeated API calls)
        videos = services.get_youtube_channel_videos(user['channel_id'], max_results=50)
        
        # Find the specific video
        video_details = next((v for v in videos if v['video_id'] == video_id), None)
        
        if not video_details:
            return jsonify({'error': 'Video not found in your channel'}), 404
        
        # Try to get additional details like captions availability
        has_captions = video_details.get('has_captions', False)
        
        return jsonify({
            'video': video_details,
            'has_captions': has_captions,
            'video_url': f'https://www.youtube.com/watch?v={video_id}',
            'success': True
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching video details for {video_id}: {e}")
        return jsonify({'error': f'Failed to fetch video details: {str(e)}'}), 500

# MOCK / UTILITY APIs (keeping existing functionality)
@bp.route('/api/generate-script', methods=['POST'])
@login_required
def generate_script():
    data = request.get_json()
    prompt = f"Create a YouTube script for a video with the topic of \"{data.get('topic')}\"."
    script = services.watsonx_ai.generate_content(prompt, data.get('model_id'))
    response_data = {"script": script, "suggestions": "Consider a strong call-to-action."}
    database.save_analysis_data(session['user_id'], 'script', None, None, f"Script: {data.get('topic')}", response_data, {})
    return jsonify(response_data)

@bp.route('/api/generate-calendar', methods=['POST'])
@login_required
def generate_calendar_route():
    data = request.get_json()
    calendar_result = utils.generate_smart_calendar_content(data.get('content_goals'), data.get('platforms'), data.get('posting_frequency'), int(data.get('content_duration')))
    recommendations = utils.generate_ai_recommendations(calendar_result, data.get('content_goals'), data.get('platforms'))
    predictions = utils.generate_performance_predictions(calendar_result['metrics'], data.get('platforms'))
    response_data = {
        'calendar_items': calendar_result['calendar_items'], 'recommendations': recommendations, 'predictions': predictions,
        'metrics': calendar_result['metrics'], 'success': True, 'ibm_ai_powered': services.watsonx_ai.is_available
    }
    database.save_analysis_data(session['user_id'], 'calendar', None, None, f"Smart Calendar for {data.get('content_goals')}", response_data, {})
    return jsonify(response_data)

@bp.route('/api/list-models')
@login_required
def list_models():
    models = [
        {"label": "Granite 13B Chat v2", "model_id": "ibm/granite-13b-chat-v2", "provider": "IBM"},
        {"label": "Llama 3 8B Instruct", "model_id": "meta-llama/llama-3-8b-instruct", "provider": "Meta"},
    ]
    return jsonify({"resources": models})

@bp.route('/api/list-tasks')
@login_required
def list_tasks():
    return jsonify({"resources": [{"label": "Generation", "task_id": "generation"}, {"label": "Summarization", "task_id": "summarization"}]})
    
@bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    stats = database.get_dashboard_stats(session['user_id'])
    return jsonify(stats)