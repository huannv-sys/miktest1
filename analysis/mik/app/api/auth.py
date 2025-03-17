from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
import logging
from app.database.crud import (
    get_user_by_username,
    create_user,
    get_all_users,
    delete_user,
    update_user
)
from app.utils.security import verify_password, hash_password

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

# Login form class
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login form and handler"""
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = get_user_by_username(username)
        
        if not user or not verify_password(password, user.password_hash):
            flash('Invalid username or password', 'danger')
            return render_template('login.html', form=form)
        
        # Create tokens
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        
        # Prepare response
        resp = redirect(url_for('main_bp.dashboard'))
        
        # Set cookies
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        
        return resp
    
    return render_template('login.html', form=form)

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API login endpoint for programmatic access"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Missing username or password"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    user = get_user_by_username(username)
    
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Create tokens
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    })

@auth_bp.route('/logout', methods=['GET'])
def logout():
    """User logout"""
    resp = redirect(url_for('auth_bp.login'))
    unset_jwt_cookies(resp)
    return resp

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    
    return jsonify({
        "access_token": access_token
    })

# User management API endpoints
@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users"""
    current_user = get_jwt_identity()
    user = get_user_by_username(current_user)
    
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403
    
    users = get_all_users()
    return jsonify([user.to_dict() for user in users])

@auth_bp.route('/users', methods=['POST'])
@jwt_required()
def add_user():
    """Add a new user"""
    current_user = get_jwt_identity()
    admin_user = get_user_by_username(current_user)
    
    if not admin_user or admin_user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403
    
    data = request.json
    
    # Validate required fields
    required_fields = ['username', 'password', 'email', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if username already exists
    existing_user = get_user_by_username(data['username'])
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409
    
    # Validate role
    valid_roles = ['admin', 'user', 'operator']
    if data['role'] not in valid_roles:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}), 400
    
    # Create user
    try:
        hashed_password = hash_password(data['password'])
        user = create_user(
            username=data['username'],
            password=hashed_password,
            email=data['email'],
            role=data['role']
        )
        return jsonify(user.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({"error": f"Error creating user: {str(e)}"}), 500

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_route(user_id):
    """Update a user"""
    current_user = get_jwt_identity()
    admin_user = get_user_by_username(current_user)
    
    if not admin_user or admin_user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403
    
    data = request.json
    
    # Update user
    try:
        password_hash = None
        if data.get('password'):
            password_hash = hash_password(data['password'])
        
        updated_user = update_user(
            user_id,
            username=data.get('username'),
            password=password_hash,
            email=data.get('email'),
            role=data.get('role')
        )
        
        if not updated_user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify(updated_user.to_dict())
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({"error": f"Error updating user: {str(e)}"}), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user_route(user_id):
    """Delete a user"""
    current_user = get_jwt_identity()
    admin_user = get_user_by_username(current_user)
    
    if not admin_user or admin_user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403
    
    # Prevent deleting your own account
    if str(admin_user.id) == str(user_id):
        return jsonify({"error": "Cannot delete your own account"}), 400
    
    result = delete_user(user_id)
    if not result:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"message": "User deleted successfully"})

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_current_user_profile():
    """Get current user profile"""
    current_username = get_jwt_identity()
    user = get_user_by_username(current_username)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Return user data without password hash
    user_data = user.to_dict()
    return jsonify(user_data)
