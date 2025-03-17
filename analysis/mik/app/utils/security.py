import logging
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

# Configure logger
logger = logging.getLogger(__name__)

def hash_password(password):
    """Generate a password hash"""
    return generate_password_hash(password)

def verify_password(password, password_hash):
    """Verify a password against a hash"""
    return check_password_hash(password_hash, password)

def generate_random_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_tokens(identity):
    """Generate JWT access and refresh tokens"""
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

def sanitize_input(input_str):
    """Sanitize input to prevent injection attacks"""
    if input_str is None:
        return None
    
    # Replace potentially dangerous characters
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '&': '&amp;'
    }
    
    for char, replacement in replacements.items():
        input_str = input_str.replace(char, replacement)
    
    return input_str
