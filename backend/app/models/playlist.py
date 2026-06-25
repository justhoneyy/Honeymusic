import uuid
from datetime import datetime
from app.extensions import db

class Playlist(db.Model):
    __tablename__ = 'playlists'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(500))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    is_collaborative = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(7), default='#1DB954')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    songs = db.relationship('PlaylistSong', backref='playlist', lazy='dynamic',
                           order_by='PlaylistSong.position', cascade='all, delete-orphan')

    def to_dict(self):
        songs_list = self.songs.order_by(PlaylistSong.position).all()
        song_count = len(songs_list)
        total_duration = sum(ps.song.duration for ps in songs_list if ps.song) if songs_list else 0
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cover_url': self.cover_url,
            'user_id': self.user_id,
            'username': self.owner.username if self.owner else None,
            'is_public': self.is_public,
            'is_collaborative': self.is_collaborative,
            'color': self.color,
            'song_count': song_count,
            'total_duration': total_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PlaylistSong(db.Model):
    __tablename__ = 'playlist_songs'

    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.String(36), db.ForeignKey('playlists.id'), nullable=False)
    song_id = db.Column(db.String(36), db.ForeignKey('songs.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    added_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('playlist_id', 'song_id', name='uq_playlist_song'),
        db.Index('idx_playlist_position', 'playlist_id', 'position'),
    )


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.String(36), db.ForeignKey('songs.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'song_id', name='uq_user_song_like'),
        db.Index('idx_user_likes', 'user_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'song_id': self.song_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
