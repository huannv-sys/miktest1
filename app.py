from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import logging

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)

# Create a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///mikrotik_monitor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Initialize SQLAlchemy with the app
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
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
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

# Device model 
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
    
    user = db.relationship('User', backref=db.backref('devices', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'port': self.port,
            'username': self.username,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/devices')
@login_required
def devices():
    return render_template('devices.html', devices=[])

@app.route('/vpn-monitoring')
@login_required
def vpn_monitoring():
    devices = Device.query.all()
    return render_template('vpn_monitoring.html', devices=devices)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất thành công', 'success')
    return redirect(url_for('index'))

@app.route('/api/vpn/<int:device_id>')
@login_required
def api_vpn_data(device_id):
    # Mô phỏng dữ liệu API cho frontend
    device = Device.query.get_or_404(device_id)
    
    # Trong thực tế, chúng ta sẽ gọi API của MikroTik từ đây
    # Hiện tại, trả về dữ liệu mẫu để test frontend
    return jsonify({
        'total_connections': 5,
        'connections_by_type': {
            'pptp': 2,
            'l2tp': 1,
            'sstp': 0,
            'ovpn': 2
        },
        'active_connections': [
            {
                'id': '1',
                'user': 'user1',
                'service': 'pptp',
                'address': '203.0.113.45',
                'local_address': '10.10.10.2',
                'uptime': '2h 15m',
                'bytes_in': 367001600,  # 350 MB
                'bytes_out': 125829120  # 120 MB
            },
            {
                'id': '2',
                'user': 'user2',
                'service': 'pptp',
                'address': '203.0.113.82',
                'local_address': '10.10.10.3',
                'uptime': '4h 10m',
                'bytes_in': 524288000,  # 500 MB
                'bytes_out': 209715200  # 200 MB
            },
            {
                'id': '3',
                'user': 'user3',
                'service': 'l2tp',
                'address': '198.51.100.72',
                'local_address': '10.10.10.4',
                'uptime': '1h 30m',
                'bytes_in': 157286400,  # 150 MB
                'bytes_out': 83886080   # 80 MB
            },
            {
                'id': '4',
                'user': 'user4',
                'service': 'ovpn',
                'address': '198.51.100.15',
                'local_address': '10.10.10.5',
                'uptime': '5h 45m',
                'bytes_in': 734003200,  # 700 MB
                'bytes_out': 314572800  # 300 MB
            },
            {
                'id': '5',
                'user': 'user5',
                'service': 'ovpn',
                'address': '198.51.100.28',
                'local_address': '10.10.10.6',
                'uptime': '0h 45m',
                'bytes_in': 52428800,   # 50 MB
                'bytes_out': 31457280   # 30 MB
            }
        ],
        'server_config': {
            'pptp': {
                'enabled': True,
                'port': 1723,
                'authentication': ['mschap2', 'mschap1']
            },
            'l2tp': {
                'enabled': True,
                'port': 1701,
                'authentication': ['mschap2']
            },
            'sstp': {
                'enabled': False,
                'port': 443,
                'authentication': []
            },
            'ovpn': {
                'enabled': True,
                'port': 1194,
                'mode': 'tcp',
                'authentication': ['certificate']
            }
        }
    })

# API endpoint to export VPN data
@app.route('/api/vpn/<int:device_id>/export')
@login_required
def api_vpn_export(device_id):
    # Mô phỏng xuất dữ liệu VPN
    device = Device.query.get_or_404(device_id)
    
    # Trong thực tế, chúng ta sẽ truy vấn dữ liệu thật và xuất ra
    return jsonify({
        'status': 'success',
        'message': 'VPN data exported successfully',
        'filename': f'vpn_data_{device.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    })

@app.route('/status')
def status():
    return jsonify({
        'status': 'ok',
        'message': 'MikroTik Monitor API is running'
    })

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)