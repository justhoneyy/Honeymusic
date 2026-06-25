from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.playlist import Playlist, PlaylistSong
from app.models.music import Song
from app.utils.helpers import create_response

playlists_bp = Blueprint('api.playlists', __name__)

@playlists_bp.route('', methods=['GET'])
@jwt_required()
def get_playlists():
    user_id = get_jwt_identity()
    playlists = Playlist.query.filter_by(user_id=user_id)\
        .order_by(Playlist.updated_at.desc()).all()
    return create_response(data=[p.to_dict() for p in playlists])

@playlists_bp.route('', methods=['POST'])
@jwt_required()
def create_playlist():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'name' not in data:
        return create_response(error='Playlist name is required', status=400)
    
    playlist = Playlist(
        name=data['name'],
        description=data.get('description', ''),
        cover_url=data.get('cover_url'),
        user_id=user_id,
        is_public=data.get('is_public', True),
        is_collaborative=data.get('is_collaborative', False),
        color=data.get('color', '#1DB954')
    )
    db.session.add(playlist)
    db.session.commit()
    return create_response(data=playlist.to_dict(), message='Playlist created', status=201)

@playlists_bp.route('/<playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return create_response(error='Playlist not found', status=404)
    if not playlist.is_public:
        from flask_jwt_extended import verify_jwt_in_request
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if playlist.user_id != user_id:
                return create_response(error='Private playlist', status=403)
        except:
            return create_response(error='Private playlist', status=403)

    data = playlist.to_dict()
    songs = []
    for ps in playlist.songs.order_by(PlaylistSong.position).all():
        song_data = ps.song.to_dict() if ps.song else None
        if song_data:
            song_data['added_at'] = ps.added_at.isoformat() if ps.added_at else None
            song_data['added_by'] = ps.added_by
            songs.append(song_data)
    data['songs'] = songs
    return create_response(data=data)

@playlists_bp.route('/<playlist_id>', methods=['PUT'])
@jwt_required()
def update_playlist(playlist_id):
    user_id = get_jwt_identity()
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return create_response(error='Playlist not found', status=404)
    if playlist.user_id != user_id:
        return create_response(error='Not authorized', status=403)

    data = request.get_json() or {}
    for field in ['name', 'description', 'cover_url', 'is_public', 'is_collaborative', 'color']:
        if field in data:
            setattr(playlist, field, data[field])
    
    db.session.commit()
    return create_response(data=playlist.to_dict(), message='Playlist updated')

@playlists_bp.route('/<playlist_id>', methods=['DELETE'])
@jwt_required()
def delete_playlist(playlist_id):
    user_id = get_jwt_identity()
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return create_response(error='Playlist not found', status=404)
    if playlist.user_id != user_id:
        return create_response(error='Not authorized', status=403)
    
    PlaylistSong.query.filter_by(playlist_id=playlist_id).delete()
    db.session.delete(playlist)
    db.session.commit()
    return create_response(message='Playlist deleted')

@playlists_bp.route('/<playlist_id>/songs', methods=['POST'])
@jwt_required()
def add_song_to_playlist(playlist_id):
    user_id = get_jwt_identity()
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return create_response(error='Playlist not found', status=404)
    if playlist.user_id != user_id and not playlist.is_collaborative:
        return create_response(error='Not authorized', status=403)

    data = request.get_json()
    if not data or 'song_id' not in data:
        return create_response(error='song_id required', status=400)

    song = Song.query.get(data['song_id'])
    if not song:
        return create_response(error='Song not found', status=404)

    existing = PlaylistSong.query.filter_by(
        playlist_id=playlist_id, song_id=data['song_id']
    ).first()
    if existing:
        return create_response(error='Song already in playlist', status=409)

    max_pos = db.session.query(db.func.max(PlaylistSong.position))\
        .filter_by(playlist_id=playlist_id).scalar()
    position = (max_pos or 0) + 1

    ps = PlaylistSong(
        playlist_id=playlist_id,
        song_id=data['song_id'],
        position=position,
        added_by=user_id
    )
    db.session.add(ps)
    db.session.commit()
    return create_response(data=ps.song.to_dict(), message='Song added to playlist', status=201)

@playlists_bp.route('/<playlist_id>/songs/<song_id>', methods=['DELETE'])
@jwt_required()
def remove_song_from_playlist(playlist_id, song_id):
    user_id = get_jwt_identity()
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return create_response(error='Playlist not found', status=404)
    if playlist.user_id != user_id:
        return create_response(error='Not authorized', status=403)

    ps = PlaylistSong.query.filter_by(
        playlist_id=playlist_id, song_id=song_id
    ).first()
    if not ps:
        return create_response(error='Song not in playlist', status=404)

    db.session.delete(ps)
    
    # Reorder remaining songs
    remaining = PlaylistSong.query.filter_by(playlist_id=playlist_id)\
        .order_by(PlaylistSong.position).all()
    for i, item in enumerate(remaining, 1):
        item.position = i
    
    db.session.commit()
    return create_response(message='Song removed from playlist')

@playlists_bp.route('/<playlist_id>/reorder', methods=['PUT'])
@jwt_required()
def reorder_playlist(playlist_id):
    user_id = get_jwt_identity()
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return create_response(error='Playlist not found', status=404)
    if playlist.user_id != user_id:
        return create_response(error='Not authorized', status=403)

    data = request.get_json()
    if not data or 'song_ids' not in data:
        return create_response(error='song_ids required', status=400)

    for i, song_id in enumerate(data['song_ids'], 1):
        ps = PlaylistSong.query.filter_by(
            playlist_id=playlist_id, song_id=song_id
        ).first()
        if ps:
            ps.position = i
    
    db.session.commit()
    return create_response(message='Playlist reordered')
