from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
import logging

# Import socketio for use in this module
from app import socketio

logger = logging.getLogger(__name__)

main_bp = Blueprint('main_bp', __name__)

# Role-based access decorator
def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required(optional=True)
        def decorator(*args, **kwargs):
            current_user = get_jwt_identity()
            if not current_user:
                return redirect(url_for('auth_bp.login'))
            
            from app.database.crud import get_user_by_username
            user = get_user_by_username(current_user)
            
            if not user or user.role != role:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('main_bp.dashboard'))
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# Main routes
@main_bp.route('/')
def index():
    return redirect(url_for('auth_bp.login'))

@main_bp.route('/dashboard')
@jwt_required()
def dashboard():
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('auth_bp.login'))
        
    from app.database.crud import get_devices_count, get_alerts_count
    devices_count = get_devices_count()
    alerts_count = get_alerts_count()
    
    return render_template('dashboard.html', 
                          active_page='dashboard',
                          devices_count=devices_count,
                          alerts_count=alerts_count)

@main_bp.route('/devices')
@jwt_required()
def devices():
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('auth_bp.login'))
    return render_template('devices.html', active_page='devices')

@main_bp.route('/monitoring')
@jwt_required()
def monitoring():
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('auth_bp.login'))
    return render_template('monitoring.html', active_page='monitoring')

@main_bp.route('/users')
@jwt_required()
@role_required('admin')
def users():
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('auth_bp.login'))
    return render_template('users.html', active_page='users')

@main_bp.route('/settings')
@jwt_required()
def settings():
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('auth_bp.login'))
    return render_template('settings.html', active_page='settings')

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    logger.debug("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    logger.debug("Client disconnected")

@socketio.on('request_update')
def handle_update_request(data):
    device_id = data.get('device_id')
    if device_id:
        from app.core.mikrotik import get_device_metrics
        from app.database.crud import get_device_by_id
        
        device = get_device_by_id(device_id)
        if device:
            metrics = get_device_metrics(device)
            socketio.emit('device_update', {'device_id': device_id, 'metrics': metrics})

# Register error handlers
def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {str(e)}")
        return render_template('500.html'), 500

# Utility function to init routes
def init_app(app):
    app.register_blueprint(main_bp)
    register_error_handlers(app)
    
    # Return the app for testing
    return app
