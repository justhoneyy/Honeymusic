import os
import re
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, jsonify

def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_upload(file, subfolder='music'):
    """Save uploaded file and return the path."""
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_path, exist_ok=True)
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        return os.path.join('uploads', subfolder, filename)
    return None

def generate_slug(text):
    """Generate a URL-friendly slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:200]

def format_duration(seconds):
    """Format duration in seconds to mm:ss or h:mm:ss."""
    if not seconds:
        return '0:00'
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f'{hours}:{minutes:02d}:{secs:02d}'
    return f'{minutes}:{secs:02d}'

def paginate(query, page=1, per_page=20):
    """Paginate a SQLAlchemy query and return results with metadata."""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [item.to_dict() for item in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    }

def create_response(data=None, message='Success', status=200, error=None):
    """Create a standardized API response."""
    response = {'status': status, 'message': message}
    if data is not None:
        response['data'] = data
    if error:
        response['error'] = error
    return jsonify(response), status
