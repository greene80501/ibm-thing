# File: config.py (Updated)
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class with all required settings."""
    
    # --- Flask Configuration ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    DATABASE = os.environ.get('DATABASE_PATH') or 'alice_insight.db'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5001))
    
    # --- YouTube Data API v3 Configuration ---
    # CRITICAL: This is required for real video data functionality
    YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
    
    # YouTube API settings
    YOUTUBE_API_VERSION = 'v3'
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    
    # --- IBM Watson NLU Configuration ---
    IBM_NLU_API_KEY = os.environ.get('IBM_NLU_API_KEY')
    IBM_NLU_URL = os.environ.get('IBM_NLU_URL')
    IBM_NLU_VERSION = os.environ.get('IBM_NLU_VERSION', '2022-04-07')
    
    # --- IBM Watsonx.ai Configuration ---
    IBM_WATSONX_API_KEY = os.environ.get('IBM_WATSONX_API_KEY')
    IBM_WATSONX_PROJECT_ID = os.environ.get('IBM_WATSONX_PROJECT_ID')
    IBM_WATSONX_URL = os.environ.get('IBM_WATSONX_URL', 'https://us-south.ml.cloud.ibm.com')
    
    # --- Application Settings ---
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Rate limiting for API calls
    YOUTUBE_API_QUOTA_LIMIT = 10000  # Daily quota limit
    RATE_LIMIT_ENABLED = True
    
    # Video caching settings
    VIDEO_CACHE_HOURS = 24  # How long to cache video data
    MAX_VIDEOS_PER_CHANNEL = 50  # Maximum videos to fetch per channel
    
    # --- Logging Configuration ---
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'False').lower() == 'true'
    LOG_FILE_PATH = os.environ.get('LOG_FILE_PATH', 'alice_insight.log')
    
    @classmethod
    def validate_configuration(cls):
        """
        Validate that all required configuration is present.
        Returns a tuple (is_valid, missing_configs, warnings)
        """
        missing_configs = []
        warnings = []
        
        # Critical configurations
        if not cls.YOUTUBE_API_KEY:
            missing_configs.append('YOUTUBE_API_KEY')
        
        # Optional but recommended configurations
        if not cls.IBM_NLU_API_KEY:
            warnings.append('IBM_NLU_API_KEY not set - sentiment analysis will be limited')
        
        if not cls.IBM_WATSONX_API_KEY:
            warnings.append('IBM_WATSONX_API_KEY not set - AI features will use fallback mode')
        
        if cls.SECRET_KEY == 'your-secret-key-change-in-production':
            warnings.append('SECRET_KEY is using default value - change for production')
        
        is_valid = len(missing_configs) == 0
        return is_valid, missing_configs, warnings
    
    @classmethod
    def get_setup_instructions(cls):
        """
        Returns setup instructions for missing configurations.
        """
        is_valid, missing_configs, warnings = cls.validate_configuration()
        
        instructions = []
        
        if 'YOUTUBE_API_KEY' in missing_configs:
            instructions.append("""
🔴 YOUTUBE_API_KEY is required for real video data:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Go to Credentials → Create Credentials → API Key
5. Copy the API key
6. Add to your .env file: YOUTUBE_API_KEY=your_api_key_here

For detailed steps: https://developers.google.com/youtube/v3/getting-started
            """)
        
        if 'IBM_NLU_API_KEY' in missing_configs:
            instructions.append("""
🟡 IBM_NLU_API_KEY is optional but recommended for sentiment analysis:

1. Go to IBM Cloud: https://cloud.ibm.com/
2. Create a Natural Language Understanding service
3. Get API key from service credentials
4. Add to .env file: 
   IBM_NLU_API_KEY=your_api_key
   IBM_NLU_URL=your_service_url
            """)
        
        if warnings:
            instructions.append("\n🟡 WARNINGS:")
            for warning in warnings:
                instructions.append(f"   - {warning}")
        
        return "\n".join(instructions)


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # More lenient rate limiting for development
    RATE_LIMIT_ENABLED = False
    
    # Shorter cache times for development
    VIDEO_CACHE_HOURS = 1


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    LOG_TO_FILE = True
    
    # Stricter security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Enable rate limiting
    RATE_LIMIT_ENABLED = True
    
    # Production database settings
    DATABASE = os.environ.get('DATABASE_PATH') or '/app/data/alice_insight.db'


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    DEBUG = True
    DATABASE = ':memory:'  # Use in-memory database for tests
    
    # Disable external API calls during testing
    YOUTUBE_API_KEY = 'test_key'
    IBM_NLU_API_KEY = 'test_key'
    
    # Disable rate limiting for tests
    RATE_LIMIT_ENABLED = False


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}