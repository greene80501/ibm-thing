# File: app/__init__.py
from flask import Flask
import logging
from config import Config

def create_app(config_class=Config):
    """
    Creates and configures an instance of the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    app.logger = logger

    # --- Initialize Extensions and Services ---
    from . import database
    database.init_app(app)

    # --- Register Blueprints ---
    from . import auth
    app.register_blueprint(auth.bp)

    from . import routes
    app.register_blueprint(routes.bp)
    
    # Make the root path redirect to the dashboard (or login)
    app.add_url_rule('/', endpoint='routes.index')

    # --- Register Context Processors ---
    from . import utils
    app.context_processor(utils.utility_processor)

    logger.info("✅ Alice Insight Suite application created successfully.")
    logger.info(f"🔵 IBM NLU: {'CONFIGURED' if app.config.get('IBM_NLU_API_KEY') else 'NOT CONFIGURED'}")
    logger.info(f"🔵 YouTube API: {'CONFIGURED' if app.config.get('YOUTUBE_API_KEY') else 'NOT CONFIGURED'}")
    
    return app