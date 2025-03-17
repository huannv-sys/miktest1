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
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")
    
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
    
    # Register blueprints
    from app.api.devices import devices_bp
    from app.api.auth import auth_bp
    from app.api.monitoring import monitoring_bp
    from app.api.config import config_bp
    from app.api.topology import topology_bp
    
    app.register_blueprint(devices_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(topology_bp)
    
    # Register main routes
    from app.main import main_bp, init_app as init_main
    init_main(app)
    
    # Add template context processors
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return {
            'now': datetime.now
        }
    
    # Create database tables
    with app.app_context():
        from app.database import models
        db.create_all()
        
        # Create admin user if not exists
        from app.database.crud import get_user_by_username, create_user
        from app.utils.security import hash_password
        
        admin_user = get_user_by_username("admin")
        if not admin_user:
            create_user(
                username="admin",
                password=hash_password("admin"),
                email="admin@example.com",
                role="admin"
            )
            logger.info("Admin user created")
    
    return app

# Load app for gunicorn
app = create_app()
