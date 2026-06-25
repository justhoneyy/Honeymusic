import uuid
from datetime import datetime
from app.extensions import db

class ListenHistory(db.Model):
    __tablename__ = 'listen_history'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.String(36), db.ForeignKey('songs.id'), nullable=False)
    played_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration_played = db.Column(db.Integer, default=0)  # seconds
    completed = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(50), default='library')  # playlist, album, search, recommendation
    device = db.Column(db.String(50), default='web')
    ip_address = db.Column(db.String(45))

    __table_args__ = (
        db.Index('idx_user_listen_history', 'user_id', 'played_at'),
        db.Index('idx_song_plays', 'song_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'song_id': self.song_id,
            'played_at': self.played_at.isoformat() if self.played_at else None,
            'duration_played': self.duration_played,
            'completed': self.completed,
            'source': self.source,
            'device': self.device,
        }


class Analytics(db.Model):
    __tablename__ = 'analytics'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.Date, nullable=False, index=True)
    total_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    premium_users = db.Column(db.Integer, default=0)
    total_plays = db.Column(db.BigInteger, default=0)
    unique_songs_played = db.Column(db.Integer, default=0)
    total_playlists = db.Column(db.Integer, default=0)
    total_songs = db.Column(db.Integer, default=0)
    storage_used = db.Column(db.BigInteger, default=0)  # bytes
    api_requests = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('date', name='uq_analytics_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_users': self.total_users,
            'new_users': self.new_users,
            'active_users': self.active_users,
            'premium_users': self.premium_users,
            'total_plays': self.total_plays,
            'unique_songs_played': self.unique_songs_played,
            'total_playlists': self.total_playlists,
            'total_songs': self.total_songs,
            'storage_used': self.storage_used,
            'api_requests': self.api_requests,
        }
