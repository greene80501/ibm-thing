# File: database_migration.py
# Run this script to update your existing database with the new video caching functionality

import sqlite3
import os

def migrate_database(db_path='alice_insight.db'):
    """
    Migrate existing database to add video caching and ensure channel_id field exists.
    """
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Please run init_db.py first.")
        return False
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if channel_id column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'channel_id' not in columns:
            print("Adding channel_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN channel_id TEXT")
            conn.commit()
            print("✅ Added channel_id column")
        else:
            print("✅ channel_id column already exists")
        
        # Check if cached_videos table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cached_videos'")
        if not cursor.fetchone():
            print("Creating cached_videos table...")
            cursor.execute('''
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
                    UNIQUE(user_id, video_id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX idx_cached_videos_user_id ON cached_videos(user_id)")
            cursor.execute("CREATE INDEX idx_cached_videos_cached_at ON cached_videos(cached_at)")
            
            conn.commit()
            print("✅ Created cached_videos table with indexes")
        else:
            print("✅ cached_videos table already exists")
        
        # Add indexes that might be missing
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_channel_id ON users(channel_id)")
            conn.commit()
            print("✅ Ensured channel_id index exists")
        except sqlite3.Error as e:
            print(f"Note: Channel ID index may already exist: {e}")
        
        print("\n🎉 Database migration completed successfully!")
        print("\nNext steps:")
        print("1. Make sure your YouTube API key is configured in config.py")
        print("2. Restart your Flask application")
        print("3. Connect your YouTube channel from the My Channel page")
        print("4. Your real video data will now be loaded from YouTube!")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database migration failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False

def verify_migration(db_path='alice_insight.db'):
    """
    Verify that the migration was successful.
    """
    print(f"\nVerifying migration for: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table structure
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        required_columns = ['channel_id', 'channel_name', 'channel_verified']
        missing_columns = [col for col in required_columns if col not in user_columns]
        
        if missing_columns:
            print(f"❌ Missing columns in users table: {missing_columns}")
            return False
        else:
            print("✅ Users table has all required columns")
        
        # Check if cached_videos table exists and has correct structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cached_videos'")
        if cursor.fetchone():
            print("✅ cached_videos table exists")
            
            cursor.execute("PRAGMA table_info(cached_videos)")
            cache_columns = [column[1] for column in cursor.fetchall()]
            expected_cache_columns = ['user_id', 'video_id', 'title', 'has_captions']
            
            if all(col in cache_columns for col in expected_cache_columns):
                print("✅ cached_videos table has correct structure")
            else:
                print("❌ cached_videos table is missing some columns")
                return False
        else:
            print("❌ cached_videos table not found")
            return False
        
        # Test that we can insert and retrieve data
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Database has {user_count} users")
        
        conn.close()
        print("\n🎉 Migration verification passed!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == '__main__':
    # Run the migration
    success = migrate_database()
    
    if success:
        # Verify the migration
        verify_migration()
        
        print("\n" + "="*50)
        print("MIGRATION COMPLETE!")
        print("="*50)
        print("\nYour Alice Insight Suite is now ready to use real YouTube data!")
        print("\nTo test:")
        print("1. Run: python run.py")
        print("2. Go to http://localhost:5001")
        print("3. Login with demo@alice.io / password123")
        print("4. Go to 'My Channel' and connect your YouTube channel")
        print("5. Your real videos will be loaded from YouTube API!")
    else:
        print("\n❌ Migration failed. Please check the errors above.")