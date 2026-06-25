from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.music import Song
from app.models.analytics import ListenHistory
from app.utils.helpers import create_response

player_bp = Blueprint('api.player', __name__)

@player_bp.route('/queue', methods=['GET'])
@jwt_required()
def get_queue():
    user_id = get_jwt_identity()
    # Get last played as queue context (simplified - production would use Redis)
    recent = ListenHistory.query.filter_by(user_id=user_id)\
        .order_by(ListenHistory.played_at.desc()).limit(20).all()
    
    queue = []
    for h in recent:
        if h.song:
            queue.append(h.song.to_dict())
    
    return create_response(data={'queue': queue})

@player_bp.route('/recently-played', methods=['GET'])
@jwt_required()
def recently_played():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 10, type=int)
    
    # Get unique recently played songs
    recent = db.session.query(Song).join(
        ListenHistory, ListenHistory.song_id == Song.id
    ).filter(
        ListenHistory.user_id == user_id
    ).order_by(
        ListenHistory.played_at.desc()
    ).distinct(Song.id).limit(limit).all()

    return create_response(data=[s.to_dict() for s in recent])
