import uuid
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.user import User, UserPreference, TokenBlocklist

class AuthService:
    @staticmethod
    def register(email, username, password, display_name=None):
        """Register a new user with email and password."""
        if User.query.filter_by(email=email).first():
            return None, 'Email already registered'
        if User.query.filter_by(username=username).first():
            return None, 'Username already taken'

        user = User(
            email=email,
            username=username,
            display_name=display_name or username,
            auth_provider='email'
        )
        user.set_password(password)
        db.session.add(user)

        # Create default preferences
        prefs = UserPreference(user_id=user.id)
        db.session.add(prefs)
        db.session.commit()

        return user, None

    @staticmethod
    def login(email, password):
        """Authenticate user with email and password."""
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return None, 'Invalid email or password'

        user.last_seen = datetime.utcnow()
        db.session.commit()

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return {
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }, None

    @staticmethod
    def google_auth(google_id, email, display_name, avatar_url):
        """Authenticate or register user via Google OAuth."""
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                user.google_id = google_id
                user.auth_provider = 'google'
                user.avatar_url = avatar_url
            else:
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f'{base_username}{counter}'
                    counter += 1
                user = User(
                    email=email,
                    username=username,
                    display_name=display_name,
                    google_id=google_id,
                    avatar_url=avatar_url,
                    auth_provider='google',
                    is_verified=True
                )
                db.session.add(user)
                prefs = UserPreference(user_id=user.id)
                db.session.add(prefs)

        user.last_seen = datetime.utcnow()
        db.session.commit()

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return {
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }, None

    @staticmethod
    def logout(jti, token_type, user_id, expires_at):
        """Revoke a JWT token."""
        blocklist = TokenBlocklist(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(blocklist)
        db.session.commit()
        return True

    @staticmethod
    def refresh_token(identity):
        """Generate new tokens."""
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
        }
