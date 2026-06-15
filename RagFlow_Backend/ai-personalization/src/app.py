"""
app.py — AI Personalization Service (RAGFlow Integration)

Minimal Flask application that serves as the RAGFlow API interface.
All RAGFlow endpoints are handled by the ragflow_routes blueprint.

This service acts as a thin wrapper around RAGFlow, providing:
- Health checks
- RAGFlow API proxying via /api/ragflow/* routes
- Database integration with Supabase
"""

import os
import traceback
from dotenv import load_dotenv
from routes.public_auth_routes import public_auth_bp
from routes.public_chat_routes import public_chat_bp
from lesson_planner_routes import lesson_bp
# Load environment variables from root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

from flask import Flask, jsonify
from flask_cors import CORS

# Import RAGFlow routes
from ragflow_routes import ragflow_bp

# Initialize database
from supabase_client import db

print("\n" + "=" * 80)
print("INITIALIZING AI PERSONALIZATION SERVICE")
print("=" * 80)

app = Flask(__name__)
CORS(app)

app.register_blueprint(ragflow_bp)
app.register_blueprint(public_auth_bp)
app.register_blueprint(public_chat_bp)
app.register_blueprint(lesson_bp)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for service monitoring."""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'ai-personalization',
            'ragflow_enabled': True,
        })
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'ai-personalization',
            'error': str(e),
        }), 500

# ─────────────────────────────────────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────────────────────────────────────


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Route not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    print(f"[ERROR] Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Server Startup
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5001))
    flask_env = os.getenv('FLASK_ENV', 'development').lower()
    if flask_env == 'production':
        debug_mode = False
    else:
        debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ['true', '1', 'yes']
    print(f"\n[INFO] AI Personalization Service starting on port {port}")
    print(f"[INFO] Environment: {flask_env.upper()}")
    print(f"[INFO] Debug Mode: {'ENABLED' if debug_mode else 'DISABLED'}")
    print(f"[INFO] RAGFlow Integration: ENABLED")
    print(f"[INFO] CORS: Enabled")
    print(f"[INFO] Gemini API: {'Configured' if os.getenv('GEMINI_API_KEY') else 'Not configured'}\n")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
