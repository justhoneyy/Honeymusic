import os
import uuid
from datetime import datetime
from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.user import User, UserPreference
from app.utils.helpers import create_response, paginate

users_bp = Blueprint('users', __name__)

ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

def allowed_avatar_file(filename):
    """Check if uploaded file has an allowed extension for avatars."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS

# ---------------------------------------------------------------------------
# GET /api/users/profile - Get current user's full profile
# ---------------------------------------------------------------------------
@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Retrieve the authenticated user's full profile information."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return create_response(error='User not found', status=404)
    
    data = user.to_dict(include_sensitive=True)
    if user.preferences:
        data['preferences'] = user.preferences.to_dict()
    
    return create_response(data=data)


# ---------------------------------------------------------------------------
# PUT /api/users/profile - Update current user's profile
# ---------------------------------------------------------------------------
@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update the authenticated user's profile information."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return create_response(error='User not found', status=404)

    data = request.get_json()
    if not data:
        return create_response(error='No data provided', status=400)

    # Track what changed
    changes = []

    # Update display name
    if 'display_name' in data:
        new_name = data['display_name'].strip()
        if new_name:
            user.display_name = new_name
            changes.append('display_name')
        else:
            return create_response(error='Display name cannot be empty', status=400)

    # Update bio
    if 'bio' in data:
        user.bio = data['bio'].strip() if data['bio'] else ''
        changes.append('bio')

    # Update username
    if 'username' in data:
        new_username = data['username'].strip().lower()
        if not new_username:
            return create_response(error='Username cannot be empty', status=400)
        
        # Check uniqueness
        existing = User.query.filter(
            User.username == new_username,
            User.id != user_id
        ).first()
        if existing:
            return create_response(error='Username already taken', status=409)
        
        user.username = new_username
        changes.append('username')

    # Update email
    if 'email' in data:
        new_email = data['email'].strip().lower()
        if not new_email:
            return create_response(error='Email cannot be empty', status=400)
        
        existing = User.query.filter(
            User.email == new_email,
            User.id != user_id
        ).first()
        if existing:
            return create_response(error='Email already in use', status=409)
        
        user.email = new_email
        user.is_verified = False  # Require re-verification on email change
        changes.append('email')

    # Update password
    if 'current_password' in data and 'new_password' in data:
        if not user.check_password(data['current_password']):
            return create_response(error='Current password is incorrect', status=403)
        
        if len(data['new_password']) < 8:
            return create_response(error='New password must be at least 8 characters', status=400)
        
        user.set_password(data['new_password'])
        changes.append('password')

    if not changes:
        return create_response(error='No valid fields to update', status=400)

    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return create_response(
        data=user.to_dict(include_sensitive=True),
        message=f'Profile updated: {", ".join(changes)}'
    )


# ---------------------------------------------------------------------------
# POST /api/users/avatar - Upload a new avatar image
# ---------------------------------------------------------------------------
@users_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload a new avatar image for the authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return create_response(error='User not found', status=404)

    if 'avatar' not in request.files:
        return create_response(error='No file provided. Use field name "avatar"', status=400)

    file = request.files['avatar']
    if file.filename == '':
        return create_response(error='No file selected', status=400)

    if not allowed_avatar_file(file.filename):
        return create_response(
            error=f'Invalid file type. Allowed: {", ".join(ALLOWED_AVATAR_EXTENSIONS)}',
            status=400
        )

    try:
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'avatar_{user_id}_{uuid.uuid4().hex[:8]}.{ext}'
        
        # Ensure directory exists
        upload_path = os.path.join(
            current_app.root_path, '..', 
            current_app.config.get('UPLOAD_FOLDER', 'uploads'),
            'avatars'
        )
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        # Update user avatar URL
        avatar_url = f'/uploads/avatars/{filename}'
        
        # Delete old avatar if exists
        if user.avatar_url:
            old_path = os.path.join(
                current_app.root_path, '..',
                user.avatar_url.lstrip('/')
            )
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass  # Ignore deletion errors

        user.avatar_url = avatar_url
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return create_response(
            data={'avatar_url': avatar_url},
            message='Avatar uploaded successfully'
        )

    except Exception as e:
        current_app.logger.error(f'Avatar upload failed: {str(e)}')
        return create_response(error='Failed to upload avatar', status=500)


# ---------------------------------------------------------------------------
# DELETE /api/users/avatar - Remove current avatar
# ---------------------------------------------------------------------------
@users_bp.route('/avatar', methods=['DELETE'])
@jwt_required()
def delete_avatar():
    """Remove the current avatar and reset to default."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return create_response(error='User not found', status=404)

    if user.avatar_url:
        # Delete file
        try:
            old_path = os.path.join(
                current_app.root_path, '..',
                user.avatar_url.lstrip('/')
            )
            if os.path.exists(old_path):
                os.remove(old_path)
        except OSError:
            pass

        user.avatar_url = None
        user.updated_at = datetime.utcnow()
        db.session.commit()

    return create_response(message='Avatar removed')


# ---------------------------------------------------------------------------
# GET /api/users/preferences - Get user preferences
# PUT /api/users/preferences - Update user preferences
# ---------------------------------------------------------------------------
@users_bp.route('/preferences', methods=['GET', 'PUT'])
@jwt_required()
def handle_preferences():
    """Get or update user preferences (theme, playback settings, etc.)."""
    user_id = get_jwt_identity()
    
    # Ensure preferences record exists
    prefs = UserPreference.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = UserPreference(user_id=user_id)
        db.session.add(prefs)
        db.session.commit()

    if request.method == 'GET':
        return create_response(data=prefs.to_dict())

    # PUT - Update preferences
    data = request.get_json()
    if not data:
        return create_response(error='No data provided', status=400)

    # Fields that can be updated
    valid_fields = [
        'theme', 'crossfade', 'crossfade_duration', 'gapless_playback',
        'audio_quality', 'volume', 'playback_speed', 'equalizer_preset',
        'notification_enabled', 'autoplay', 'show_explicit', 'language'
    ]

    updates = []
    for field in valid_fields:
        if field in data:
            value = data[field]
            
            # Validation
            if field == 'theme' and value not in ('dark', 'light'):
                continue
            if field == 'audio_quality' and value not in ('low', 'medium', 'high', 'lossless'):
                continue
            if field == 'volume':
                value = max(0.0, min(1.0, float(value)))
            if field == 'playback_speed':
                value = max(0.5, min(2.0, float(value)))
            if field == 'crossfade_duration':
                value = max(0, min(30, int(value)))
            if field == 'equalizer_preset' and value not in (
                'flat', 'pop', 'rock', 'jazz', 'classical', 'bass', 'treble', 'custom'
            ):
                continue
            if field == 'language' and len(value) > 10:
                continue

            setattr(prefs, field, value)
            updates.append(field)

    if updates:
        prefs.updated_at = datetime.utcnow()
        db.session.commit()
        return create_response(
            data=prefs.to_dict(),
            message=f'Preferences updated: {", ".join(updates)}'
        )

    return create_response(data=prefs.to_dict(), message='No changes made')


# ---------------------------------------------------------------------------
# GET /api/users/history - Get listening history (paginated)
# ---------------------------------------------------------------------------
@users_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """Retrieve the authenticated user's listening history with pagination."""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Clamp values
    page = max(1, page)
    per_page = max(1, min(50, per_page))

    from app.models.analytics import ListenHistory
    
    history = ListenHistory.query.filter_by(user_id=user_id)\
        .order_by(ListenHistory.played_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for h in history.items:
        item = h.to_dict()
        if h.song:
            item['song'] = h.song.to_dict()
        items.append(item)

    return create_response(data={
        'items': items,
        'page': history.page,
        'per_page': history.per_page,
        'total': history.total,
        'pages': history.pages,
        'has_next': history.has_next,
        'has_prev': history.has_prev,
    })


# ---------------------------------------------------------------------------
# DELETE /api/users/history - Clear listening history
# ---------------------------------------------------------------------------
@users_bp.route('/history', methods=['DELETE'])
@jwt_required()
def clear_history():
    """Clear the authenticated user's entire listening history."""
    user_id = get_jwt_identity()
    
    from app.models.analytics import ListenHistory
    
    count = ListenHistory.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return create_response(
        message=f'Cleared {count} entries from listening history'
    )


# ---------------------------------------------------------------------------
# GET /api/users/public/<user_id> - Get public profile of any user
# ---------------------------------------------------------------------------
@users_bp.route('/public/<user_id>', methods=['GET'])
def get_public_profile(user_id):
    """Get a public user profile (no sensitive info)."""
    user = User.query.get(user_id)
    if not user:
        return create_response(error='User not found', status=404)

    # Count public playlists
    from app.models.playlist import Playlist
    public_playlists = Playlist.query.filter_by(
        user_id=user_id, is_public=True
    ).count()

    # Count total likes
    from app.models.playlist import Like
    likes_count = Like.query.filter_by(user_id=user_id).count()

    data = {
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name or user.username,
        'avatar_url': user.avatar_url,
        'bio': user.bio,
        'is_verified': user.is_verified,
        'public_playlists': public_playlists,
        'likes_count': likes_count,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }

    return create_response(data=data)


# ---------------------------------------------------------------------------
# GET /api/users/me - Shortcut alias for /api/auth/me
# ---------------------------------------------------------------------------
@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """Alias for /api/auth/me - returns current user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return create_response(error='User not found', status=404)
    return create_response(data=user.to_dict(include_sensitive=True))
