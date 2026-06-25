from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.user import User

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_premium:
            return jsonify({'error': 'Premium subscription required'}), 403
        return f(*args, **kwargs)
    return decorated_function
