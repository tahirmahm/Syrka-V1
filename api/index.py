"""Vercel serverless entry point for Syrka."""

# Import the FastAPI app
import sys
from pathlib import Path

# Add the syrka directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "syrka"))

from app.main import app

# Vercel expects the app to be named 'app' or exported as handler
handler = app
