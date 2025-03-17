import logging
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from cryptography.fernet import Fernet
import base64
import os
from hashlib import sha256

# Configure logger
logger = logging.getLogger(__name__)

# Encryption key for device passwords
# In production, this should be stored in environment variables
# and not in the code
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

# Initialize the Fernet cipher
_cipher = None
try:
    if not ENCRYPTION_KEY:
        # Generate a key if not set - this is just for development
        # In production, a fixed key should be used to ensure passwords remain decryptable
        logger.warning("ENCRYPTION_KEY not set, generating a temporary one")
        ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode()
        
    # Ensure the key is properly formatted for Fernet
    # Check if key is already in correct format
    if len(base64.urlsafe_b64decode(ENCRYPTION_KEY.encode() + b'=' * (-len(ENCRYPTION_KEY) % 4))) != 32:
        # If not properly formatted, create a valid key
        logger.warning("ENCRYPTION_KEY not correctly formatted, converting to valid Fernet key")
        key = base64.urlsafe_b64encode(sha256(ENCRYPTION_KEY.encode()).digest())
        _cipher = Fernet(key)
    else:
        # Key is in correct format
        _cipher = Fernet(ENCRYPTION_KEY.encode())
except Exception as e:
    logger.error(f"Error initializing encryption cipher: {str(e)}")
    # Create a new valid key as fallback
    logger.warning("Creating new Fernet key as fallback")
    key = base64.urlsafe_b64encode(os.urandom(32))
    _cipher = Fernet(key)

def hash_password(password):
    """Generate a password hash for user authentication"""
    return generate_password_hash(password)

def verify_password(password, password_hash):
    """Verify a password against a hash for user authentication"""
    return check_password_hash(password_hash, password)

def encrypt_device_password(password):
    """Encrypt a device password"""
    if not password:
        return None
    if not _cipher:
        logger.error("Encryption cipher not initialized")
        return None
    try:
        return _cipher.encrypt(password.encode()).decode()
    except Exception as e:
        logger.error(f"Error encrypting password: {str(e)}")
        return None

def decrypt_device_password(encrypted_password):
    """Decrypt a device password"""
    if not encrypted_password:
        return None
    if not _cipher:
        logger.error("Encryption cipher not initialized")
        return None
    try:
        return _cipher.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        logger.error(f"Error decrypting password: {str(e)}")
        return None

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
