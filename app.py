from flask import Flask, render_template, request, jsonify
import re
import requests
import time
from googleapiclient.discovery import build
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException

# ------------------------------------------------------------------
# --- Alice Insight Suite - Main Application File
# ------------------------------------------------------------------

app = Flask(__name__)

# --- API Configuration ---
YOUTUBE_API_KEY = "AIzaSyBb0GIb6f6H-uukICrV4KTQMU3FKAuKKwM"
IBM_NLU_API_KEY = "BunpkLiLUfJB4e1-sq1-3P_8f2LqzbqN5Vbe4L2UA9KR"
IBM_NLU_URL = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/dead8d2a-3978-4e15-b413-dab9e0ae7f46"
IBM_NLU_VERSION = "2022-04-07"
WATSONX_API_KEY = "nYQ1gFsdCOfpCL5oOZj3-b18q5-2RsZXTn1JsydVmTbV"
WATSONX_PROJECT_ID = "a03dfd66-1d06-4458-badb-82229d245571"
WATSONX_URL = "https://us-south.ml.cloud.ibm.com"

# --- API Client Initialization ---
try:
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
except Exception as e:
    print(f"CRITICAL: Could not initialize YouTube client: {e}")
    youtube = None

try:
    nlu_authenticator = IAMAuthenticator(IBM_NLU_API_KEY)
    nlu_client = NaturalLanguageUnderstandingV1(version=IBM_NLU_VERSION, authenticator=nlu_authenticator)
    nlu_client.set_service_url(IBM_NLU_URL)
except Exception as e:
    print(f"CRITICAL: Could not initialize NLU client: {e}")
    nlu_client = None

# --- Helper Functions ---
def get_video_id_from_url(url):
    """Extracts the YouTube video ID from various URL formats."""
    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    return video_id_match.group(0) if video_id_match else None

def get_youtube_comments(video_id, max_results=50):
    """Fetches public comments from a YouTube video."""
    if not youtube: return []
    try:
        req = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_results, textFormat="plainText")
        res = req.execute()
        return [{"id": item["id"], "text": item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]} for item in res.get("items", [])]
    except Exception as e:
        print(f"Error fetching YouTube comments: {e}")
        return []

def get_watsonx_iam_token():
    """Generates an IAM token for watsonx.ai authentication."""
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={WATSONX_API_KEY}"
    try:
        res = requests.post("https://iam.cloud.ibm.com/identity/token", headers=headers, data=data)
        res.raise_for_status()
        return res.json().get("access_token")
    except Exception as e:
        print(f"Error getting IAM token: {e}")
        return None

# --- Page Rendering Routes ---
@app.route('/')
def index(): return render_template('index.html')
@app.route('/sentiment-analyzer')
def sentiment_analyzer(): return render_template('sentiment_analyzer.html')
@app.route('/theme-clustering')
def theme_clustering(): return render_template('theme_clustering.html')
@app.route('/competitor-dashboard')
def competitor_dashboard(): return render_template('competitor_dashboard.html')
@app.route('/script-helper')
def script_helper(): return render_template('script_helper.html')

# ------------------------------------------------------------------
# --- API Endpoints
# ------------------------------------------------------------------

@app.route('/api/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    video_url = request.json.get('video_url')
    video_id = get_video_id_from_url(video_url)
    if not video_id: return jsonify({"error": "Invalid YouTube URL"}), 400
    if not nlu_client: return jsonify({"error": "NLU client not initialized"}), 500
    comments = get_youtube_comments(video_id, max_results=40)
    if not comments: return jsonify({"error": "Could not fetch comments or no comments found."}), 404
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    emotion_counts = {"joy": 0, "anger": 0, "sadness": 0, "surprise": 0, "disgust": 0}
    for comment in comments:
        if len(comment['text'].split()) < 3: continue
        try:
            analysis = nlu_client.analyze(text=comment['text'], features={'sentiment': {}, 'emotion': {}}).get_result()
            sentiment = analysis.get('sentiment', {}).get('document', {}).get('label', 'neutral')
            sentiment_counts[sentiment] += 1
            emotions = analysis.get('emotion', {}).get('document', {}).get('emotion', {})
            if emotions:
                dominant_emotion = max(emotions, key=emotions.get)
                if dominant_emotion in emotion_counts:
                    emotion_counts[dominant_emotion] += 1
            time.sleep(0.25)
        except ApiException as e:
            print(f"NLU API Error (Code: {e.code}): {e.message}")
        except Exception as e:
            print(f"An unexpected error occurred during analysis: {e}")
    alert = ""
    if comments and (sentiment_counts['negative'] / len(comments) > 0.4):
        alert = "Alert: High spike in negative sentiment detected!"
    return jsonify({"sentiment_data": sentiment_counts, "emotion_data": emotion_counts, "alert": alert})

@app.route('/api/cluster-themes', methods=['POST'])
def cluster_themes():
    video_url = request.json.get('video_url')
    video_id = get_video_id_from_url(video_url)
    if not video_id: return jsonify({"error": "Invalid YouTube URL"}), 400
    comments = get_youtube_comments(video_id, max_results=80)
    if not comments: return jsonify({"error": "Could not fetch comments."}), 404
    categorized_comments = {}
    for comment in comments:
        if len(comment['text'].split()) < 4: continue
        try:
            analysis = nlu_client.analyze(text=comment['text'], features={'categories': {'limit': 1}}).get_result()
            category = analysis.get('categories', [])
            if category and category[0]['score'] > 0.5:
                label = " -> ".join(category[0]['label'].strip('/').split('/'))
                categorized_comments.setdefault(label, []).append(comment['id'])
            time.sleep(0.25)
        except ApiException as e:
            print(f"NLU API Error during clustering (Code: {e.code}): {e.message}")
    clusters = [{"summary": label, "comment_ids": ids} for label, ids in categorized_comments.items() if len(ids) > 2]
    outliers = [{"summary": label, "comment_ids": ids} for label, ids in categorized_comments.items() if len(ids) <= 2]
    return jsonify({"clusters": clusters, "outliers": outliers})

@app.route('/api/analyze-competitors', methods=['POST'])
def analyze_competitors():
    usernames = request.json.get('usernames', [])
    data = []
    if not youtube: return jsonify({"error": "YouTube client not initialized"}), 500
    for name in usernames:
        try:
            search_res = youtube.search().list(part="snippet", q=name, type="channel", maxResults=1).execute()
            if not search_res.get('items'): continue
            channel_id = search_res['items'][0]['id']['channelId']
            channel_res = youtube.channels().list(part="statistics,snippet", id=channel_id).execute()
            stats = channel_res['items'][0]['statistics']
            snippet = channel_res['items'][0]['snippet']
            data.append({"username": snippet['title'], "subscribers": int(stats.get('subscriberCount', 0)), "avg_engagement_rate": 0.045, "recent_sentiment": "positive"})
        except Exception as e:
            print(f"Error fetching competitor data for {name}: {e}")
    return jsonify({"competitors": data})

@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    topic = request.json.get('topic')
    model_id = request.json.get('model_id', 'ibm/granite-13b-chat-v2') # Default to Granite

    full_prompt = f"""You are a helpful assistant who creates scripts for YouTube content creators.
**Task:** Create a script for a vertical YouTube Short (under 60 seconds) about the topic: "{topic}".
**Style:** The tone should be energetic, friendly, and use simple language suitable for a wide audience.
**Structure:** Follow this exact structure:
- **Hook (0-3 seconds):** An irresistible opening line.
- **Body:** The main points of the video, explained simply.
- **CTA (Call to Action):** A clear call to like, comment, or follow.
- **Visuals/Sounds:** Suggest simple visuals or sound ideas for each part.
"""
    
    token = get_watsonx_iam_token()
    if not token: return jsonify({"error": "Failed to authenticate with watsonx.ai"}), 500
        
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    json_data = {
        'model_id': model_id,
        'project_id': WATSONX_PROJECT_ID,
        'input': full_prompt,
        'parameters': {'max_new_tokens': 600, 'min_new_tokens': 100},
    }

    try:
        api_url = f'{WATSONX_URL}/ml/v1/text/generation?version=2024-05-31'
        response = requests.post(api_url, headers=headers, json=json_data)
        response.raise_for_status()
        result = response.json()
        generated_script = result['results'][0]['generated_text']
        suggestion = "Consider adding trending background music to boost engagement."
        return jsonify({"script": generated_script, "suggestions": suggestion})
    except requests.exceptions.HTTPError as e:
        error_text = e.response.text
        print(f"HTTP Error generating script with watsonx.ai: {e.response.status_code} - {error_text}")
        if "model_not_supported" in error_text:
             return jsonify({"error": f"Model '{model_id}' is not supported by your project. Please choose another model."}), 400
        return jsonify({"error": f"Failed to generate script. API responded with status {e.response.status_code}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred generating script: {e}")
        return jsonify({"error": "An unexpected error occurred while generating the script."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)