-- File: app/database.sql (Updated)
-- Users table with comprehensive channel information
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    channel_url TEXT,
    channel_id TEXT,  -- YouTube channel ID (important for API calls)
    channel_name TEXT,
    channel_subscriber_count INTEGER DEFAULT 0,
    channel_video_count INTEGER DEFAULT 0,
    channel_view_count INTEGER DEFAULT 0,
    channel_thumbnail TEXT,
    channel_description TEXT,
    channel_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis storage table
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,  -- 'sentiment', 'theme_cluster', 'competitor', 'script', 'calendar'
    video_url TEXT,
    video_id TEXT,
    title TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON data
    metadata TEXT,       -- Additional JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Video cache table (NEW - for caching YouTube API responses)
CREATE TABLE cached_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_id TEXT NOT NULL,
    title TEXT NOT NULL,
    thumbnail_url TEXT,
    published_at TEXT,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    duration TEXT,
    has_captions BOOLEAN DEFAULT FALSE,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE(user_id, video_id)  -- Prevent duplicate cache entries
);

-- Indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_channel_id ON users(channel_id);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_created_at ON analyses(created_at);
CREATE INDEX idx_cached_videos_user_id ON cached_videos(user_id);
CREATE INDEX idx_cached_videos_cached_at ON cached_videos(cached_at);

-- Triggers to update timestamps (optional but helpful)
CREATE TRIGGER update_users_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Insert a demo user for testing (optional)
-- Password is 'password123' hashed with bcrypt
INSERT INTO users (email, password_hash, channel_url, channel_id, channel_name, channel_subscriber_count, channel_video_count, channel_view_count, channel_verified) VALUES 
('demo@alice.io', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4d/eUO6K46', 'https://youtube.com/@demo', 'UC_demo_channel_id', 'Demo Channel', 10000, 25, 500000, TRUE);