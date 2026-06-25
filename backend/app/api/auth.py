from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token
)
from app.services.auth_service import AuthService
from app.utils.helpers import create_response

auth_bp = Blueprint('api.auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return create_response(error='Missing request body', status=400)
    
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    display_name = data.get('display_name')

    if not all([email, username, password]):
        return create_response(error='Email, username, and password are required', status=400)

    user, error = AuthService.register(email, username, password, display_name)
    if error:
        return create_response(error=error, status=409)
    
    tokens = AuthService.login(email, password)
    return create_response(data=tokens[0], message='Registration successful', status=201)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return create_response(error='Missing request body', status=400)
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return create_response(error='Email and password are required', status=400)

    result, error = AuthService.login(email, password)
    if error:
        return create_response(error=error, status=401)
    
    return create_response(data=result, message='Login successful')

@auth_bp.route('/google', methods=['POST'])
def google_auth():
    data = request.get_json()
    if not data:
        return create_response(error='Missing request body', status=400)
    
    result, error = AuthService.google_auth(
        data.get('google_id'),
        data.get('email'),
        data.get('display_name'),
        data.get('avatar_url')
    )
    if error:
        return create_response(error=error, status=400)
    
    return create_response(data=result, message='Google authentication successful')

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    tokens = AuthService.refresh_token(identity)
    return create_response(data=tokens)

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    token_type = get_jwt()['type']
    user_id = get_jwt_identity()
    expires_at = get_jwt()['exp']
    
    from datetime import datetime
    exp_datetime = datetime.fromtimestamp(expires_at)
    
    AuthService.logout(jti, token_type, user_id, exp_datetime)
    return create_response(message='Successfully logged out')

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    from app.models.user import User
    user = User.query.get(user_id)
    if not user:
        return create_response(error='User not found', status=404)
    return create_response(data=user.to_dict(include_sensitive=True))
