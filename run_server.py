import os
import logging
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the Flask application
app = Flask(__name__)

# Configure application
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_only_for_development")

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


# Define models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    devices = db.relationship('Device', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    ip_address = db.Column(db.String(64), nullable=False)
    port = db.Column(db.Integer, default=8728)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_check = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='unknown')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'port': self.port,
            'username': self.username,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'status': self.status
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Define routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', devices=devices)


@app.route('/devices')
@login_required
def devices():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('devices.html', devices=devices)


@app.route('/devices/add', methods=['GET', 'POST'])
@login_required
def add_device():
    if request.method == 'POST':
        name = request.form.get('name')
        ip_address = request.form.get('ip_address')
        port = request.form.get('port', 8728, type=int)
        username = request.form.get('username')
        password = request.form.get('password')
        use_ssl = 'use_ssl' in request.form
        notes = request.form.get('notes', '')
        
        if not all([name, ip_address, username, password]):
            flash('Vui lòng điền đầy đủ thông tin thiết bị!', 'danger')
            return render_template('device_form.html')
        
        device = Device(
            name=name,
            ip_address=ip_address,
            port=port,
            username=username,
            password=password,
            user_id=current_user.id,
            status='unknown'
        )
        
        try:
            db.session.add(device)
            db.session.commit()
            flash(f'Đã thêm thiết bị {name} thành công!', 'success')
            return redirect(url_for('devices'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding device: {str(e)}")
            flash('Đã xảy ra lỗi khi thêm thiết bị!', 'danger')
    
    return render_template('device_form.html')


@app.route('/devices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_device(id):
    device = Device.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        ip_address = request.form.get('ip_address')
        port = request.form.get('port', 8728, type=int)
        username = request.form.get('username')
        password = request.form.get('password')
        use_ssl = 'use_ssl' in request.form
        notes = request.form.get('notes', '')
        
        if not all([name, ip_address, username]):
            flash('Vui lòng điền đầy đủ thông tin thiết bị!', 'danger')
            return render_template('device_form.html', device=device)
        
        device.name = name
        device.ip_address = ip_address
        device.port = port
        device.username = username
        if password:  # Chỉ cập nhật mật khẩu nếu có nhập
            device.password = password
        # Các trường khác sẽ được thêm sau khi chỉnh sửa model
        
        try:
            db.session.commit()
            flash(f'Đã cập nhật thiết bị {name} thành công!', 'success')
            return redirect(url_for('devices'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating device: {str(e)}")
            flash('Đã xảy ra lỗi khi cập nhật thiết bị!', 'danger')
    
    return render_template('device_form.html', device=device)


@app.route('/devices/<int:id>/delete', methods=['POST'])
@login_required
def delete_device(id):
    device = Device.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(device)
        db.session.commit()
        flash(f'Đã xóa thiết bị {device.name} thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting device: {str(e)}")
        flash('Đã xảy ra lỗi khi xóa thiết bị!', 'danger')
    
    return redirect(url_for('devices'))


@app.route('/vpn')
@login_required
def vpn_monitoring():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('vpn_monitoring.html', devices=devices)

@app.route('/api/vpn/<int:device_id>')
@login_required
def api_vpn_data(device_id):
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first_or_404()
    
    # Trong một ứng dụng thực tế, chúng ta sẽ gọi hàm get_vpn_stats từ mik.app.core.vpn
    # Nhưng hiện tại, chúng ta sẽ trả về dữ liệu mẫu
    vpn_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "device_id": device.id,
        "device_name": device.name,
        "total_connections": 12,
        "connections_by_type": {
            "pptp": 5,
            "l2tp": 3,
            "sstp": 0,
            "ovpn": 4,
            "ipsec": 0
        },
        "active_connections": [
            { 
                "id": 1, 
                "user": "user1", 
                "type": "pptp", 
                "service": "PPTP",
                "address": "203.0.113.45", 
                "local_address": "10.10.10.2", 
                "uptime": "2h 15m", 
                "bytes_in": 367001600, 
                "bytes_out": 125829120
            },
            { 
                "id": 2, 
                "user": "user2", 
                "type": "pptp", 
                "service": "PPTP",
                "address": "203.0.113.46", 
                "local_address": "10.10.10.3", 
                "uptime": "1h 35m", 
                "bytes_in": 156764160, 
                "bytes_out": 52428800
            },
            { 
                "id": 3, 
                "user": "user3", 
                "type": "l2tp", 
                "service": "L2TP",
                "address": "203.0.113.47", 
                "local_address": "10.10.10.4", 
                "uptime": "4h 20m", 
                "bytes_in": 524288000, 
                "bytes_out": 262144000
            },
            { 
                "id": 4, 
                "user": "user4", 
                "type": "ovpn", 
                "service": "OpenVPN",
                "address": "203.0.113.48", 
                "local_address": "10.10.10.5", 
                "uptime": "5h 45m", 
                "bytes_in": 734003200, 
                "bytes_out": 367001600
            }
        ],
        "server_config": {
            "pptp": {
                "enabled": True,
                "port": 1723,
                "max_mtu": 1450,
                "max_mru": 1450,
                "authentication": ["mschap2"]
            },
            "l2tp": {
                "enabled": True,
                "port": 1701,
                "max_mtu": 1450,
                "max_mru": 1450,
                "authentication": ["mschap2"]
            },
            "sstp": {
                "enabled": False,
                "port": 443,
                "max_mtu": 0,
                "max_mru": 0,
                "authentication": []
            },
            "ovpn": {
                "enabled": True,
                "port": 1194,
                "mode": "ip",
                "authentication": ["certificate"]
            },
            "ipsec": {
                "enabled": False,
                "policy_count": 0,
                "proposals": []
            }
        }
    }
    
    return vpn_data

@app.route('/api/vpn/<int:device_id>/export')
@login_required
def api_vpn_export(device_id):
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first_or_404()
    
    # Trong một ứng dụng thực tế, chúng ta sẽ gọi hàm get_vpn_stats từ mik.app.core.vpn
    # Nhưng hiện tại, chúng ta sẽ trả về dữ liệu mẫu giống như trên
    vpn_data = {
        "device_id": device.id,
        "device_name": device.name,
        "export_time": datetime.utcnow().isoformat(),
        "connections": [
            { 
                "id": 1, 
                "user": "user1", 
                "type": "pptp", 
                "service": "PPTP",
                "address": "203.0.113.45", 
                "local_address": "10.10.10.2", 
                "uptime": "2h 15m", 
                "bytes_in": 367001600, 
                "bytes_out": 125829120
            },
            { 
                "id": 2, 
                "user": "user2", 
                "type": "pptp", 
                "service": "PPTP",
                "address": "203.0.113.46", 
                "local_address": "10.10.10.3", 
                "uptime": "1h 35m", 
                "bytes_in": 156764160, 
                "bytes_out": 52428800
            },
            { 
                "id": 3, 
                "user": "user3", 
                "type": "l2tp", 
                "service": "L2TP",
                "address": "203.0.113.47", 
                "local_address": "10.10.10.4", 
                "uptime": "4h 20m", 
                "bytes_in": 524288000, 
                "bytes_out": 262144000
            },
            { 
                "id": 4, 
                "user": "user4", 
                "type": "ovpn", 
                "service": "OpenVPN",
                "address": "203.0.113.48", 
                "local_address": "10.10.10.5", 
                "uptime": "5h 45m", 
                "bytes_in": 734003200, 
                "bytes_out": 367001600
            }
        ]
    }
    
    return vpn_data
