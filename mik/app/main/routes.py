from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from mik.app.main import bp
from mik.app.models import User, Device
from mik.app import db
from mik.app.mikrotik import get_device_connection, get_system_info, get_interfaces, get_device_clients
from datetime import datetime

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page:
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', devices=devices)

@bp.route('/devices')
@login_required
def devices():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('devices.html', devices=devices)

@bp.route('/device/add', methods=['GET', 'POST'])
@login_required
def add_device():
    if request.method == 'POST':
        name = request.form.get('name')
        ip_address = request.form.get('ip_address')
        port = request.form.get('port', type=int, default=8728)
        username = request.form.get('username')
        password = request.form.get('password')
        
        device = Device(name=name, ip_address=ip_address, port=port,
                       username=username, password=password, user_id=current_user.id)
        
        try:
            # Thử kết nối đến thiết bị
            api = get_device_connection(device)
            if api:
                # Lấy thông tin hệ thống để xác nhận thiết bị hoạt động
                system_info = get_system_info(api)
                if system_info:
                    device.status = 'online'
                    device.last_check = datetime.utcnow()
                    db.session.add(device)
                    db.session.commit()
                    flash('Device added successfully')
                    return redirect(url_for('main.devices'))
            
            flash('Could not connect to device')
            return redirect(url_for('main.add_device'))
            
        except Exception as e:
            flash(f'Error adding device: {str(e)}')
            return redirect(url_for('main.add_device'))
    
    return render_template('device_form.html')

@bp.route('/device/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_device(id):
    device = Device.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        device.name = request.form.get('name')
        device.ip_address = request.form.get('ip_address')
        device.port = request.form.get('port', type=int, default=8728)
        device.username = request.form.get('username')
        if request.form.get('password'):
            device.password = request.form.get('password')
        
        try:
            db.session.commit()
            flash('Device updated successfully')
            return redirect(url_for('main.devices'))
        except Exception as e:
            flash(f'Error updating device: {str(e)}')
            return redirect(url_for('main.edit_device', id=id))
    
    return render_template('device_form.html', device=device)

@bp.route('/device/<int:id>/delete')
@login_required
def delete_device(id):
    device = Device.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(device)
        db.session.commit()
        flash('Device deleted successfully')
    except Exception as e:
        flash(f'Error deleting device: {str(e)}')
    
    return redirect(url_for('main.devices'))

@bp.route('/api/devices')
@login_required
def api_devices():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return jsonify([device.to_dict() for device in devices])

@bp.route('/api/device/<int:id>')
@login_required
def api_device(id):
    device = Device.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    try:
        api = get_device_connection(device)
        if api:
            system_info = get_system_info(api)
            interfaces = get_interfaces(api)
            clients = get_device_clients(api)
            
            return jsonify({
                'device': device.to_dict(),
                'system_info': system_info,
                'interfaces': interfaces,
                'clients': clients
            })
        
        return jsonify({'error': 'Could not connect to device'})
    except Exception as e:
        return jsonify({'error': str(e)})

@bp.route('/vpn-monitoring')
@login_required
def vpn_monitoring():
    """VPN Monitoring page"""
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('vpn_monitoring.html', devices=devices)