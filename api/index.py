# Vercel serverless entry point — imports the Flask app from web/app.py
import sys
import os
from pathlib import Path

# Ensure project root is on path so comp_engine and web.app resolve correctly
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from web.app import app  # noqa: F401 — Vercel picks up 'app' by convention
