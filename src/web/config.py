from flask import Flask
from pathlib import Path
from flask_cors import CORS

# Create Flask app
app = Flask(__name__,
           template_folder=Path(__file__).parent / 'templates',
           static_folder=Path(__file__).parent / 'static')
CORS(app)

# Configure app
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    UPLOAD_FOLDER=Path(__file__).parent / 'static/uploads',
    RESULTS_FOLDER=Path(__file__).parent / 'static/results'
) 