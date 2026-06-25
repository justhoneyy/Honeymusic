import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import Config
from app.extensions import db, migrate, bcrypt, jwt, cors, login_manager

load_dotenv()


def create_app(config_class=Config):
    """Application factory for Honey Music."""

    # Project root (Honeymusic/)
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    # Frontend folder
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        static_url_path=""
    )

    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    login_manager.init_app(app)
    login_manager.login_view = "api.auth.login"

    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.music import music_bp
    from app.api.playlists import playlists_bp
    from app.api.search import search_bp
    from app.api.player import player_bp
    from app.api.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(music_bp, url_prefix="/api/music")
    app.register_blueprint(playlists_bp, url_prefix="/api/playlists")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(player_bp, url_prefix="/api/player")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Health check
    @app.route("/api/health")
    def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "app": "Honey Music"
        }

    # Serve frontend
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        file_path = os.path.join(FRONTEND_DIR, path)

        if path and os.path.isfile(file_path):
            return send_from_directory(FRONTEND_DIR, path)

        return send_from_directory(FRONTEND_DIR, "index.html")

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    # Create database tables
    with app.app_context():
        from app.models import user, music, playlist, analytics
        db.create_all()

    return app
