from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
cors = CORS()
login_manager = LoginManager()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.models.user import TokenBlocklist
    jti = jwt_payload['jti']
    return TokenBlocklist.is_jti_blocklisted(jti)

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return {'error': 'Token has been revoked'}, 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {'error': 'Token has expired'}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {'error': 'Invalid token'}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {'error': 'Authorization token is missing'}, 401
