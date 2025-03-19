import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)

# Khởi tạo cơ sở dữ liệu
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Cấu hình ứng dụng
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Khởi tạo các extension
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    # Đăng ký các blueprint
    from mik.app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Khởi tạo cơ sở dữ liệu
    with app.app_context():
        db.create_all()
    
    return app