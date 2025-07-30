# File: run.py
import os
from app import create_app, database

# Create the Flask app instance using the app factory
app = create_app()

if __name__ == '__main__':
    # Ensure the database exists before running
    # This is a simple check; for production, you might use Flask-Migrate
    with app.app_context():
        if not os.path.exists(app.config['DATABASE']):
            print("Database not found. Initializing...")
            database.init_db_command()
            print("Database initialized.")

    # Get configuration from the app context
    is_debug = app.config.get('DEBUG', True)
    port = app.config.get('PORT', 5001)
    host = app.config.get('HOST', '0.0.0.0')

    print(f"🚀 Starting Alice Insight Suite on http://{host}:{port} (Debug: {is_debug})")
    app.run(debug=is_debug, port=port, host=host)