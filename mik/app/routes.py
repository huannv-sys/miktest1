from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from . import models
from . import db

def init_routes(app):
    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember', False)
            
            user = models.User.query.filter_by(username=username).first()
            
            if user is None or not user.check_password(password):
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))
                
            login_user(user, remember=remember)
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
                
            return redirect(next_page)
            
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/devices')
    @login_required
    def devices():
        devices = models.Device.query.all()
        return render_template('devices.html', devices=devices)

    @app.route('/device/add', methods=['GET', 'POST'])
    @login_required
    def add_device():
        if request.method == 'POST':
            name = request.form.get('name')
            ip_address = request.form.get('ip_address')
            port = request.form.get('port', 8728)
            username = request.form.get('username')
            password = request.form.get('password')
            
            device = models.Device(
                name=name,
                ip_address=ip_address,
                port=port,
                username=username,
                password=password,
                user_id=current_user.id
            )
            db.session.add(device)
            db.session.commit()
            
            flash('Device added successfully', 'success')
            return redirect(url_for('devices'))
            
        return render_template('device_form.html')

    @app.route('/device/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_device(id):
        device = models.Device.query.get_or_404(id)
        
        if request.method == 'POST':
            device.name = request.form.get('name')
            device.ip_address = request.form.get('ip_address')
            device.port = request.form.get('port', 8728)
            device.username = request.form.get('username')
            
            # Only update password if provided
            if request.form.get('password'):
                device.password = request.form.get('password')
                
            db.session.commit()
            flash('Device updated successfully', 'success')
            return redirect(url_for('devices'))
            
        return render_template('device_form.html', device=device)

    @app.route('/device/<int:id>/delete')
    @login_required
    def delete_device(id):
        device = models.Device.query.get_or_404(id)
        db.session.delete(device)
        db.session.commit()
        flash('Device deleted successfully', 'success')
        return redirect(url_for('devices'))

    # API Routes
    @app.route('/api/devices')
    @login_required
    def api_devices():
        devices = models.Device.query.all()
        return jsonify([device.to_dict() for device in devices])

    @app.route('/api/device/<int:id>')
    @login_required
    def api_device(id):
        device = models.Device.query.get_or_404(id)
        return jsonify(device.to_dict())