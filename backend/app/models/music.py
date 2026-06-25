import uuid
from datetime import datetime
from app.extensions import db

class Genre(db.Model):
    __tablename__ = 'genres'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    color = db.Column(db.String(7))  # hex color
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    songs = db.relationship('Song', backref='genre', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'image_url': self.image_url,
            'color': self.color,
            'song_count': self.songs.count(),
        }


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    cover_url = db.Column(db.String(500))
    monthly_listeners = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    albums = db.relationship('Album', backref='artist', lazy='dynamic', cascade='all, delete-orphan')
    songs = db.relationship('Song', backref='artist', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'bio': self.bio,
            'image_url': self.image_url,
            'cover_url': self.cover_url,
            'monthly_listeners': self.monthly_listeners,
            'verified': self.verified,
            'album_count': self.albums.count(),
            'song_count': self.songs.count(),
        }


class Album(db.Model):
    __tablename__ = 'albums'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    artist_id = db.Column(db.String(36), db.ForeignKey('artists.id'), nullable=False)
    cover_url = db.Column(db.String(500))
    release_date = db.Column(db.Date)
    album_type = db.Column(db.String(20), default='album')  # album, single, ep, compilation
    label = db.Column(db.String(200))
    description = db.Column(db.Text)
    total_tracks = db.Column(db.Integer, default=0)
    total_duration = db.Column(db.Integer, default=0)  # seconds
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    songs = db.relationship('Song', backref='album', lazy='dynamic', 
                           order_by='Song.track_number', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'artist_id': self.artist_id,
            'artist_name': self.artist.name if self.artist else None,
            'cover_url': self.cover_url,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'album_type': self.album_type,
            'label': self.label,
            'description': self.description,
            'total_tracks': self.total_tracks,
            'total_duration': self.total_duration,
            'is_featured': self.is_featured,
        }


class Song(db.Model):
    __tablename__ = 'songs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.String(36), db.ForeignKey('artists.id'), nullable=False)
    album_id = db.Column(db.String(36), db.ForeignKey('albums.id'), nullable=True)
    genre_id = db.Column(db.String(36), db.ForeignKey('genres.id'), nullable=True)
    duration = db.Column(db.Integer, default=0)  # seconds
    track_number = db.Column(db.Integer, default=1)
    disc_number = db.Column(db.Integer, default=1)
    audio_url = db.Column(db.String(500), nullable=False)
    cover_url = db.Column(db.String(500))
    lyrics = db.Column(db.Text, nullable=True)
    explicit = db.Column(db.Boolean, default=False)
    plays = db.Column(db.BigInteger, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_podcast = db.Column(db.Boolean, default=False)
    bitrate = db.Column(db.Integer, default=320)
    file_format = db.Column(db.String(10), default='mp3')
    file_size = db.Column(db.BigInteger, default=0)
    bpm = db.Column(db.Integer, nullable=True)
    key = db.Column(db.String(5), nullable=True)
    mood = db.Column(db.String(50), nullable=True)
    isrc = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    playlist_songs = db.relationship('PlaylistSong', backref='song', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='song', lazy='dynamic', cascade='all, delete-orphan')
    listen_history = db.relationship('ListenHistory', backref='song', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_artist=True, include_album=True):
        data = {
            'id': self.id,
            'title': self.title,
            'duration': self.duration,
            'duration_formatted': f'{self.duration // 60}:{self.duration % 60:02d}',
            'track_number': self.track_number,
            'disc_number': self.disc_number,
            'audio_url': self.audio_url,
            'cover_url': self.cover_url or (self.album.cover_url if self.album else None),
            'lyrics': self.lyrics,
            'explicit': self.explicit,
            'plays': self.plays,
            'is_podcast': self.is_podcast,
            'bitrate': self.bitrate,
            'file_format': self.file_format,
            'bpm': self.bpm,
            'key': self.key,
            'mood': self.mood,
            'genre_id': self.genre_id,
            'genre_name': self.genre.name if self.genre else None,
        }
        if include_artist:
            data['artist'] = self.artist.to_dict() if self.artist else None
        if include_album:
            data['album'] = self.album.to_dict() if self.album else None
        return data


class Podcast(db.Model):
    __tablename__ = 'podcasts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(500))
    author = db.Column(db.String(200))
    publisher = db.Column(db.String(200))
    language = db.Column(db.String(10), default='en')
    explicit = db.Column(db.Boolean, default=False)
    total_episodes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    episodes = db.relationship('PodcastEpisode', backref='podcast', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cover_url': self.cover_url,
            'author': self.author,
            'publisher': self.publisher,
            'language': self.language,
            'explicit': self.explicit,
            'total_episodes': self.total_episodes,
        }


class PodcastEpisode(db.Model):
    __tablename__ = 'podcast_episodes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    podcast_id = db.Column(db.String(36), db.ForeignKey('podcasts.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, default=0)
    audio_url = db.Column(db.String(500), nullable=False)
    episode_number = db.Column(db.Integer)
    season_number = db.Column(db.Integer)
    release_date = db.Column(db.Date)
    plays = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'podcast_id': self.podcast_id,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'duration_formatted': f'{self.duration // 60}:{self.duration % 60:02d}',
            'audio_url': self.audio_url,
            'episode_number': self.episode_number,
            'season_number': self.season_number,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'plays': self.plays,
        }


class Lyric(db.Model):
    __tablename__ = 'lyrics'

    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.String(36), db.ForeignKey('songs.id'), nullable=False, unique=True)
    lyrics_text = db.Column(db.Text, nullable=False)
    synced_lyrics = db.Column(db.JSON, nullable=True)  # [{"time": 12.5, "text": "..."}]
    source = db.Column(db.String(50), default='user')
    language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
