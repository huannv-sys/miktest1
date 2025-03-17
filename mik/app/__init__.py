import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
socketio = SocketIO()
jwt = JWTManager()
scheduler = BackgroundScheduler()

def create_app():
    # Create Flask app
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        logger.info(f"Using instance folder: {app.instance_path}")
    except OSError as e:
        logger.error(f"Error creating instance folder: {e}")
    
    # Load configuration
    app.config.from_object('mik.app.config.Config')
    # Secret key is set from Config object now, don't override here
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    
    # Configure CORS securely for Socket.IO
    cors_allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
    if app.config.get('DEBUG'):
        # In debug mode, allow all origins if not explicitly set
        if not cors_allowed_origins:
            socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")
            logger.warning("SECURITY WARNING: CORS is set to allow all origins in debug mode")
        else:
            # Use explicitly set origins even in debug mode
            origins = cors_allowed_origins.split(',')
            socketio.init_app(app, cors_allowed_origins=origins, async_mode="threading")
    else:
        # In production, require explicit CORS configuration
        if not cors_allowed_origins:
            # Default to localhost in production if not set
            socketio.init_app(app, cors_allowed_origins="https://localhost:5000", async_mode="threading")
            logger.warning("SECURITY WARNING: CORS_ALLOWED_ORIGINS not set, defaulting to localhost only")
        else:
            origins = cors_allowed_origins.split(',')
            socketio.init_app(app, cors_allowed_origins=origins, async_mode="threading")
    
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
    
    # Register blueprints
    from mik.app.api.devices import devices_bp
    from mik.app.api.auth import auth_bp
    from mik.app.api.monitoring import monitoring_bp
    from mik.app.api.config import config_bp
    from mik.app.api.topology import topology_bp
    
    app.register_blueprint(devices_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(topology_bp)
    
    # Register main routes
    from mik.app.main import main_bp, init_app as init_main
    init_main(app)
    
    # Add template context processors
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return {
            'now': datetime.now
        }
    
    # Initialize database 
    from mik.app.database.session import initialize_db
    initialize_db(app)
    
    # Create admin user if not exists
    try:
        with app.app_context():
            admin_username = os.environ.get("ADMIN_USERNAME")
            admin_password = os.environ.get("ADMIN_PASSWORD")
            admin_email = os.environ.get("ADMIN_EMAIL")
            
            if admin_username and admin_password and admin_email:
                from mik.app.database.crud import get_user_by_username, create_user
                from mik.app.utils.security import hash_password
                
                admin_user = get_user_by_username(admin_username)
                if not admin_user:
                    create_user(
                        username=admin_username,
                        password=hash_password(admin_password),
                        email=admin_email,
                        role="admin"
                    )
                    logger.info(f"Admin user '{admin_username}' created")
            else:
                # For development only, create a default admin in debug mode
                if app.config.get("DEBUG"):
                    from mik.app.database.crud import get_user_by_username, create_user
                    from mik.app.utils.security import hash_password, generate_random_password
                    
                    # Check if admin exists
                    admin_user = get_user_by_username("admin")
                    if not admin_user:
                        # Use a fixed password for development
                        admin_password = "admin"
                        create_user(
                            username="admin",
                            password=hash_password(admin_password),
                            email="admin@example.com",
                            role="admin"
                        )
                        logger.info(f"Development admin user created with password: {admin_password}")
                        logger.info("SECURITY WARNING: Change admin password and use environment variables in production")
    except Exception as e:
        logger.error(f"Error setting up admin user: {str(e)}")
    
    return app

# Load app for gunicorn
app = create_app()
