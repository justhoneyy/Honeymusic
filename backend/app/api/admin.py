from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app.extensions import db
from app.models.user import User
from app.models.music import Song, Album, Artist, Genre
from app.models.playlist import Playlist, Like
from app.models.analytics import ListenHistory, Analytics
from app.utils.decorators import admin_required
from app.utils.helpers import create_response

admin_bp = Blueprint('api.admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def dashboard():
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    total_users = User.query.count()
    new_users_today = User.query.filter(
        func.date(User.created_at) == today
    ).count()
    active_users = User.query.filter(
        func.date(User.last_seen) >= week_ago
    ).count()
    premium_users = User.query.filter_by(is_premium=True).count()
    total_plays = db.session.query(func.sum(Song.plays)).scalar() or 0
    total_songs = Song.query.count()
    total_playlists = Playlist.query.count()

    return create_response(data={
        'total_users': total_users,
        'new_users_today': new_users_today,
        'active_users': active_users,
        'premium_users': premium_users,
        'total_plays': total_plays,
        'total_songs': total_songs,
        'total_playlists': total_playlists,
        'date': today.isoformat(),
    })

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@admin_required
def get_analytics():
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    history = db.session.query(
        func.date(ListenHistory.played_at).label('date'),
        func.count(ListenHistory.id).label('plays'),
        func.count(func.distinct(ListenHistory.user_id)).label('unique_users')
    ).filter(
        ListenHistory.played_at >= since
    ).group_by(
        func.date(ListenHistory.played_at)
    ).order_by('date').all()

    top_songs = db.session.query(
        Song, func.count(ListenHistory.id).label('play_count')
    ).join(
        ListenHistory, ListenHistory.song_id == Song.id
    ).filter(
        ListenHistory.played_at >= since
    ).group_by(Song.id).order_by(desc('play_count')).limit(10).all()

    return create_response(data={
        'daily_plays': [
            {'date': h.date.isoformat(), 'plays': h.plays, 'users': h.unique_users}
            for h in history
        ],
        'top_songs': [
            {'song': song.to_dict(), 'plays': count}
            for song, count in top_songs
        ]
    })

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    users = User.query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return create_response(data={
        'items': [u.to_dict(include_sensitive=True) for u in users.items],
        'page': users.page,
        'per_page': users.per_page,
        'total': users.total,
        'pages': users.pages,
    })

@admin_bp.route('/music/add', methods=['POST'])
@jwt_required()
@admin_required
def add_music():
    data = request.get_json()
    if not data or 'title' not in data:
        return create_response(error='Title is required', status=400)
    
    from app.utils.helpers import generate_slug
    
    # Resolve artist
    artist_id = data.get('artist_id')
    if not artist_id and data.get('artist_name'):
        existing = Artist.query.filter_by(name=data['artist_name']).first()
        if existing:
            artist_id = existing.id
        else:
            artist = Artist(
                name=data['artist_name'],
                slug=generate_slug(data['artist_name'])
            )
            db.session.add(artist)
            db.session.flush()
            artist_id = artist.id

    # Resolve album
    album_id = data.get('album_id')
    if not album_id and data.get('album_title') and artist_id:
        existing = Album.query.filter_by(
            title=data['album_title'], artist_id=artist_id
        ).first()
        if existing:
            album_id = existing.id

    song = Song(
        title=data['title'],
        artist_id=artist_id,
        album_id=album_id,
        genre_id=data.get('genre_id'),
        duration=data.get('duration', 0),
        track_number=data.get('track_number', 1),
        audio_url=data.get('audio_url', ''),
        cover_url=data.get('cover_url'),
        explicit=data.get('explicit', False),
        mood=data.get('mood'),
        bpm=data.get('bpm'),
        key=data.get('key'),
    )
    db.session.add(song)
    db.session.commit()
    return create_response(data=song.to_dict(), message='Song added', status=201)
