import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Import the FastAPI app
from main import app

# Vercel expects the app to be named 'app'
# The app variable is already defined in main.py
