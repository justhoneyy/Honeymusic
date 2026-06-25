import uuid
from datetime import datetime
from flask_login import UserMixin
from flask_jwt_extended import decode_token
from app.extensions import db, bcrypt, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    display_name = db.Column(db.String(120))
    avatar_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    auth_provider = db.Column(db.String(20), default='email')  # email, google
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    preferences = db.relationship('UserPreference', backref='user', uselist=False, lazy=True)
    playlists = db.relationship('Playlist', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    listen_history = db.relationship('ListenHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'is_verified': self.is_verified,
            'is_premium': self.is_premium,
            'auth_provider': self.auth_provider,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
        }
        if include_sensitive:
            data['is_admin'] = self.is_admin
        return data

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    theme = db.Column(db.String(20), default='dark')  # dark, light
    crossfade = db.Column(db.Boolean, default=False)
    crossfade_duration = db.Column(db.Integer, default=3)  # seconds
    gapless_playback = db.Column(db.Boolean, default=True)
    audio_quality = db.Column(db.String(10), default='high')  # low, medium, high, lossless
    volume = db.Column(db.Float, default=0.8)
    playback_speed = db.Column(db.Float, default=1.0)
    equalizer_preset = db.Column(db.String(20), default='flat')
    notification_enabled = db.Column(db.Boolean, default=True)
    autoplay = db.Column(db.Boolean, default=True)
    show_explicit = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'theme': self.theme,
            'crossfade': self.crossfade,
            'crossfade_duration': self.crossfade_duration,
            'gapless_playback': self.gapless_playback,
            'audio_quality': self.audio_quality,
            'volume': self.volume,
            'playback_speed': self.playback_speed,
            'equalizer_preset': self.equalizer_preset,
            'notification_enabled': self.notification_enabled,
            'autoplay': self.autoplay,
            'show_explicit': self.show_explicit,
            'language': self.language,
        }


class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    @classmethod
    def is_jti_blocklisted(cls, jti):
        return cls.query.filter_by(jti=jti).first() is not None
