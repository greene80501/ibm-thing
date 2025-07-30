# File: app/auth.py (Updated)
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import bcrypt
from functools import wraps
from . import database, services # Changed: import services

bp = Blueprint('auth', __name__, url_prefix='/auth')

# --- Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # For API requests, return JSON error. For pages, redirect.
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Page Routes (Unchanged) ---
@bp.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard'))
    return render_template('login.html')

@bp.route('/register')
def register():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard'))
    return render_template('register.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

# --- API Routes ---
@bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    channel_url = data.get('channel_url', '').strip()

    if not all([email, password, data.get('confirm_password')]):
        return jsonify({'error': 'All fields are required'}), 400
    if password != data.get('confirm_password'):
        return jsonify({'error': 'Passwords do not match'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if database.get_user_by_email(email):
        return jsonify({'error': 'Email already registered'}), 409
    
    # --- CHANGED: Use real service to get channel data ---
    channel_data = {}
    if channel_url:
        try:
            channel_data = services.get_youtube_channel_details(channel_url)
            if not channel_data:
                # Still create user, but don't link channel and warn them
                flash('Could not verify the provided channel URL, but your account was created.', 'warning')
        except Exception as e:
            return jsonify({'error': f'Channel verification failed: {e}'}), 500

    user_id = database.create_user_with_channel(email, password, channel_url, channel_data)
    if not user_id:
        return jsonify({'error': 'Account creation failed'}), 500
        
    session['user_id'] = user_id
    session['user_email'] = email
    
    response_data = {'message': 'Account created successfully'}
    if channel_data:
        response_data['channel_verified'] = True
        response_data['channel_name'] = channel_data.get('title')
        
    return jsonify(response_data), 201

@bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
        
    user = database.get_user_by_email(email)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        return jsonify({'message': 'Login successful'})
        
    return jsonify({'error': 'Invalid email or password'}), 401