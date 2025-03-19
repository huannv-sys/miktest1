#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script để cài đặt và mở rộng module cho MikroTik Monitor
Chạy với quyền sudo: sudo python install_module.py
"""

import os
import sys
import shutil
import subprocess
import re
import argparse
import json
import datetime
import getpass
from pathlib import Path

# Màu để hiển thị trên terminal
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

# Thư mục mặc định
APP_DIR = "/opt/mikrotik-monitor"
VENV_DIR = f"{APP_DIR}/venv"
SERVICE_NAME = "mikrotik-monitor"
DEFAULT_PORT = 5050

def log_info(message):
    """Log thông tin"""
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

def log_warn(message):
    """Log cảnh báo"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")

def log_error(message):
    """Log lỗi"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def log_debug(message):
    """Log debug"""
    print(f"{Colors.BLUE}[DEBUG]{Colors.NC} {message}")

def print_header(message):
    """In tiêu đề"""
    print(f"\n{Colors.BOLD}{message}{Colors.NC}\n")

def run_command(command, shell=False):
    """Chạy lệnh shell và trả về kết quả"""
    try:
        if shell:
            process = subprocess.run(command, shell=True, check=True, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    text=True)
        else:
            process = subprocess.run(command.split(), check=True, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    text=True)
        return True, process.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_root():
    """Kiểm tra quyền root"""
    if os.geteuid() != 0:
        log_error("Script này cần chạy với quyền root. Vui lòng sử dụng sudo.")
        sys.exit(1)

def check_installation():
    """Kiểm tra cài đặt"""
    if not os.path.isdir(APP_DIR):
        log_error(f"Không tìm thấy thư mục cài đặt tại {APP_DIR}.")
        log_error("Vui lòng chạy script cài đặt trước.")
        sys.exit(1)
    
    if not os.path.isdir(VENV_DIR):
        log_warn(f"Không tìm thấy môi trường ảo Python tại {VENV_DIR}.")
        log_info("Đang tạo môi trường ảo mới...")
        success, output = run_command(f"python3 -m venv {VENV_DIR}")
        if not success:
            log_error(f"Không thể tạo môi trường ảo: {output}")
            sys.exit(1)
        
        success, _ = run_command(f"{VENV_DIR}/bin/pip install --upgrade pip")
        if not success:
            log_error("Không thể nâng cấp pip.")
    
    # Kiểm tra dịch vụ
    success, output = run_command(f"systemctl is-active {SERVICE_NAME}")
    if "inactive" in output:
        log_warn(f"Dịch vụ {SERVICE_NAME} không chạy.")
        response = input("Bạn có muốn khởi động dịch vụ không? (y/n) ")
        if response.lower() == 'y':
            success, _ = run_command(f"systemctl start {SERVICE_NAME}")
            if success:
                log_info(f"Đã khởi động dịch vụ {SERVICE_NAME}.")
            else:
                log_error(f"Không thể khởi động dịch vụ {SERVICE_NAME}.")
    
    log_info("Kiểm tra cài đặt hoàn tất.")

def check_port():
    """Kiểm tra cổng"""
    success, output = run_command(f"lsof -Pi :{DEFAULT_PORT} -sTCP:LISTEN -t")
    if success and output.strip():
        pid = output.strip()
        success, process_name = run_command(f"ps -p {pid} -o comm=")
        
        if "python" not in process_name and "gunicorn" not in process_name:
            log_warn(f"Cổng {DEFAULT_PORT} đang được sử dụng bởi tiến trình khác: {process_name.strip()} (PID: {pid}).")
            response = input("Bạn có muốn thay đổi cổng? (y/n) ")
            if response.lower() == 'y':
                new_port = input("Nhập cổng mới: ")
                update_port(new_port)
            else:
                log_warn(f"Tiếp tục với cổng {DEFAULT_PORT}. Có thể gây xung đột!")
        else:
            log_info(f"Cổng {DEFAULT_PORT} đang được sử dụng bởi ứng dụng MikroTik Monitor.")
    else:
        log_info(f"Cổng {DEFAULT_PORT} sẵn sàng để sử dụng.")

def update_port(new_port):
    """Cập nhật cổng"""
    log_info(f"Đang cập nhật cổng từ {DEFAULT_PORT} sang {new_port}...")
    
    # Cập nhật cấu hình systemd
    systemd_file = f"/etc/systemd/system/{SERVICE_NAME}.service"
    if os.path.isfile(systemd_file):
        with open(systemd_file, 'r') as f:
            content = f.read()
        
        content = content.replace(f"--bind 0.0.0.0:{DEFAULT_PORT}", f"--bind 0.0.0.0:{new_port}")
        
        with open(systemd_file, 'w') as f:
            f.write(content)
        
        run_command("systemctl daemon-reload")
    
    # Cập nhật cấu hình Nginx
    nginx_file = f"/etc/nginx/sites-available/{SERVICE_NAME}"
    if os.path.isfile(nginx_file):
        with open(nginx_file, 'r') as f:
            content = f.read()
        
        content = content.replace(f"proxy_pass http://127.0.0.1:{DEFAULT_PORT};", 
                                f"proxy_pass http://127.0.0.1:{new_port};")
        
        with open(nginx_file, 'w') as f:
            f.write(content)
        
        run_command("systemctl reload nginx")
    
    # Cập nhật biến toàn cục
    global DEFAULT_PORT
    DEFAULT_PORT = int(new_port)
    
    log_info("Đã cập nhật cổng. Đang khởi động lại dịch vụ...")
    run_command(f"systemctl restart {SERVICE_NAME}")
    log_info("Hoàn tất cập nhật cổng.")

def check_and_fix_database():
    """Kiểm tra và sửa chữa PostgreSQL"""
    log_info("Đang kiểm tra cơ sở dữ liệu PostgreSQL...")
    
    # Kiểm tra dịch vụ PostgreSQL
    success, _ = run_command("systemctl is-active postgresql")
    if not success:
        log_warn("Dịch vụ PostgreSQL không chạy.")
        log_info("Đang khởi động PostgreSQL...")
        run_command("systemctl start postgresql")
    
    # Đọc thông tin cơ sở dữ liệu từ .env
    env_file = os.path.join(APP_DIR, ".env")
    if os.path.isfile(env_file):
        db_url = None
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    db_url = line.strip().split("=", 1)[1]
                    break
        
        if db_url:
            # Phân tích DATABASE_URL để lấy thông tin
            db_match = re.match(r'postgresql://([^:]+):([^@]+)@([^:/]+):?([0-9]*)/([^?]+)', db_url)
            if db_match:
                db_user = db_match.group(1)
                db_password = db_match.group(2)
                db_host = db_match.group(3)
                db_port = db_match.group(4) or "5432"
                db_name = db_match.group(5)
                
                # Kiểm tra kết nối đến PostgreSQL
                cmd = f"sudo -u postgres psql -lqt | cut -d \\| -f 1 | grep -qw {db_name}"
                success, _ = run_command(cmd, shell=True)
                if not success:
                    log_warn(f"Không tìm thấy cơ sở dữ liệu {db_name}.")
                    response = input("Bạn có muốn tạo cơ sở dữ liệu mới không? (y/n) ")
                    if response.lower() == 'y':
                        log_info(f"Đang tạo cơ sở dữ liệu {db_name}...")
                        
                        # Tạo user nếu chưa tồn tại
                        cmd = f"sudo -u postgres psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='{db_user}';\" | grep -q 1"
                        success, _ = run_command(cmd, shell=True)
                        if not success:
                            cmd = f"sudo -u postgres psql -c \"CREATE USER {db_user} WITH PASSWORD '{db_password}';\""
                            run_command(cmd, shell=True)
                        
                        # Tạo database
                        cmd = f"sudo -u postgres psql -c \"CREATE DATABASE {db_name} OWNER {db_user};\""
                        run_command(cmd, shell=True)
                        
                        cmd = f"sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};\""
                        run_command(cmd, shell=True)
                        
                        log_info(f"Đã tạo cơ sở dữ liệu {db_name} thành công.")
                        
                        # Khởi tạo dữ liệu
                        log_info("Đang khởi tạo dữ liệu ban đầu...")
                        os.chdir(APP_DIR)
                        app_user = "mikmon"  # Mặc định
                        cmd = f"sudo -u {app_user} {VENV_DIR}/bin/python create_admin.py"
                        run_command(cmd, shell=True)
                        log_info("Đã khởi tạo dữ liệu ban đầu.")
                else:
                    log_info(f"Cơ sở dữ liệu {db_name} đã tồn tại.")
            else:
                log_error("Không thể phân tích DATABASE_URL từ file .env")
        else:
            log_error("Không tìm thấy DATABASE_URL trong file .env")
    else:
        log_error(f"Không tìm thấy file .env tại {env_file}")

def update_code():
    """Cập nhật code từ git"""
    log_info("Đang cập nhật code từ repository...")
    
    # Kiểm tra xem có phải là repository git không
    git_dir = os.path.join(APP_DIR, ".git")
    if os.path.isdir(git_dir):
        os.chdir(APP_DIR)
        
        # Lưu các thay đổi cục bộ
        success, output = run_command("git status --porcelain")
        if success and output.strip():
            log_warn("Phát hiện các thay đổi cục bộ.")
            response = input("Bạn có muốn lưu các thay đổi cục bộ trước khi cập nhật không? (y/n) ")
            if response.lower() == 'y':
                log_info("Đang tạo bản sao lưu thay đổi cục bộ...")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                patch_file = os.path.join(APP_DIR, f"local_changes_{timestamp}.patch")
                run_command(f"git diff > {patch_file}")
                log_info(f"Đã lưu thay đổi tại: {patch_file}")
        
        # Pull code mới
        log_info("Đang tải code mới từ repository...")
        success, output = run_command("git pull")
        if not success:
            log_error(f"Không thể pull code mới: {output}")
            return
        
        # Cập nhật dependencies
        log_info("Đang cập nhật dependencies...")
        req_file = os.path.join(APP_DIR, "requirements.txt")
        if os.path.isfile(req_file):
            success, output = run_command(f"{VENV_DIR}/bin/pip install -r {req_file}")
            if not success:
                log_error(f"Không thể cập nhật dependencies: {output}")
        
        # Khởi động lại dịch vụ
        log_info("Đang khởi động lại dịch vụ...")
        run_command(f"systemctl restart {SERVICE_NAME}")
        
        log_info("Đã cập nhật code thành công.")
    else:
        log_error(f"Thư mục {APP_DIR} không phải là một Git repository.")
        log_info("Bạn cần cài đặt lại ứng dụng từ git repository.")

def add_module():
    """Thêm module mới"""
    print_header("Thêm Module Mới")
    
    module_name = input("Nhập tên module: ")
    module_name = module_name.lower().replace(" ", "_")
    
    if not module_name:
        log_error("Tên module không được để trống.")
        return False
    
    # Tạo cấu trúc thư mục
    log_info(f"Đang tạo cấu trúc module {module_name}...")
    
    # Module dưới mik/app/modules
    app_module_dir = os.path.join(APP_DIR, "mik", "app", "modules")
    if not os.path.exists(app_module_dir):
        os.makedirs(app_module_dir, exist_ok=True)
    
    module_dir = os.path.join(app_module_dir, module_name)
    if os.path.exists(module_dir):
        log_error(f"Module {module_name} đã tồn tại tại {module_dir}")
        return False
    
    os.makedirs(module_dir, exist_ok=True)
    os.makedirs(os.path.join(module_dir, "templates"), exist_ok=True)
    os.makedirs(os.path.join(module_dir, "static", "js"), exist_ok=True)
    os.makedirs(os.path.join(module_dir, "static", "css"), exist_ok=True)
    
    # Tạo các file cơ bản
    # __init__.py
    init_content = f"""# Module: {module_name}

from flask import Blueprint

{module_name}_bp = Blueprint('{module_name}', __name__, 
                        url_prefix='/{module_name}',
                        template_folder='templates', 
                        static_folder='static')

from . import routes
"""
    with open(os.path.join(module_dir, "__init__.py"), 'w') as f:
        f.write(init_content)
    
    # routes.py
    routes_content = f"""# Routes for {module_name} module

from . import {module_name}_bp
from flask import render_template, jsonify, request
from flask_login import login_required


@{module_name}_bp.route('/')
@login_required
def index():
    \"\"\"Main view for {module_name} module\"\"\"
    return render_template('{module_name}/index.html', title='{module_name}')


@{module_name}_bp.route('/api/data')
@login_required
def get_data():
    \"\"\"API endpoint for {module_name} data\"\"\"
    # TODO: Implement data retrieval logic
    return jsonify({{
        'status': 'success',
        'data': []
    }})
"""
    with open(os.path.join(module_dir, "routes.py"), 'w') as f:
        f.write(routes_content)
    
    # Template
    template_dir = os.path.join(module_dir, "templates", module_name)
    os.makedirs(template_dir, exist_ok=True)
    
    template_content = f"""{% extends "base.html" %}

{% block title %}{module_name}{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <h1>{module_name}</h1>
            <hr>
            <div class="card">
                <div class="card-header">
                    <h5>Tổng quan</h5>
                </div>
                <div class="card-body">
                    <div id="{module_name}-container">
                        <p>Nội dung module {module_name} sẽ hiển thị ở đây.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('{module_name}.static', filename='js/{module_name}.js') }}"></script>
{% endblock %}
"""
    with open(os.path.join(template_dir, "index.html"), 'w') as f:
        f.write(template_content)
    
    # JavaScript
    js_content = f"""/**
 * {module_name} functionality
 */
document.addEventListener('DOMContentLoaded', function() {{
    console.log('{module_name} module initialized');
    
    // TODO: Implement module functionality
    
    // Example: Load data from API
    async function loadData() {{
        try {{
            const response = await fetch('/api/{module_name}/data');
            const data = await response.json();
            
            if (data.status === 'success') {{
                console.log('Data loaded:', data);
                // TODO: Process and display data
            }}
        }} catch (error) {{
            console.error('Error loading data:', error);
        }}
    }}
    
    // Initialize module
    loadData();
}});
"""
    with open(os.path.join(module_dir, "static", "js", f"{module_name}.js"), 'w') as f:
        f.write(js_content)
    
    # CSS
    css_content = f"""/* CSS styles for {module_name} module */
#{module_name}-container {{
    padding: 10px;
}}
"""
    with open(os.path.join(module_dir, "static", "css", f"{module_name}.css"), 'w') as f:
        f.write(css_content)
    
    # Cập nhật file __init__.py của ứng dụng để đăng ký module
    init_file = os.path.join(APP_DIR, "mik", "app", "__init__.py")
    
    if os.path.isfile(init_file):
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Kiểm tra xem đã import module chưa
        import_line = f"from mik.app.modules.{module_name} import {module_name}_bp"
        register_line = f"app.register_blueprint({module_name}_bp)"
        
        if import_line not in content:
            # Thêm import và đăng ký blueprint
            if "def create_app" in content:
                content = content.replace("from flask import Flask", 
                                        f"from flask import Flask\n{import_line}")
                
                # Thêm vào trong hàm create_app để đăng ký blueprint
                content = content.replace("app = Flask", 
                                        f"app = Flask\n    {register_line}")
            else:
                log_warn(f"Không tìm thấy hàm create_app trong {init_file}")
                log_info("Bạn cần thêm thủ công dòng sau vào nơi thích hợp:")
                print(import_line)
                print(register_line)
        
        with open(init_file, 'w') as f:
            f.write(content)
    else:
        log_warn(f"Không tìm thấy file {init_file}")
    
    # Cập nhật menu trong templates/base.html
    base_template = os.path.join(APP_DIR, "templates", "base.html")
    if os.path.isfile(base_template):
        with open(base_template, 'r') as f:
            content = f.read()
        
        # Tìm vị trí menu
        if "<li class=\"nav-item\">" in content:
            # Tạo dòng menu mới
            menu_item = f"<li class=\"nav-item\"><a class=\"nav-link\" href=\"/{module_name}\"><i class=\"fas fa-puzzle-piece\"></i> {module_name}</a></li>"
            
            # Thêm vào sau một menu item khác
            content = content.replace("<li class=\"nav-item\">", 
                                    f"<li class=\"nav-item\">\n            {menu_item}")
            
            with open(base_template, 'w') as f:
                f.write(content)
        else:
            log_warn(f"Không tìm thấy vị trí menu trong {base_template}")
    else:
        log_warn(f"Không tìm thấy file {base_template}")
    
    log_info(f"Module {module_name} đã được tạo thành công!")
    log_info(f"Đường dẫn: {module_dir}")
    log_info(f"URL: http://localhost:{DEFAULT_PORT}/{module_name}")
    
    # Khởi động lại dịch vụ
    response = input("Bạn có muốn khởi động lại dịch vụ không? (y/n) ")
    if response.lower() == 'y':
        log_info("Đang khởi động lại dịch vụ...")
        run_command(f"systemctl restart {SERVICE_NAME}")
        log_info("Đã khởi động lại dịch vụ thành công.")
    
    return True

def backup_data():
    """Backup dữ liệu"""
    print_header("Backup Dữ Liệu")
    
    backup_dir = os.path.join(APP_DIR, "backups")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"mikmon_backup_{timestamp}.tar.gz")
    
    # Tạo thư mục backup nếu chưa tồn tại
    os.makedirs(backup_dir, exist_ok=True)
    
    log_info("Đang backup dữ liệu...")
    
    # Backup database
    log_info("Đang backup cơ sở dữ liệu...")
    db_backup_file = None
    
    env_file = os.path.join(APP_DIR, ".env")
    if os.path.isfile(env_file):
        db_url = None
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    db_url = line.strip().split("=", 1)[1]
                    break
        
        if db_url:
            # Phân tích DATABASE_URL để lấy thông tin
            db_match = re.match(r'postgresql://([^:]+):([^@]+)@([^:/]+):?([0-9]*)/([^?]+)', db_url)
            if db_match:
                db_user = db_match.group(1)
                db_password = db_match.group(2)
                db_host = db_match.group(3)
                db_port = db_match.group(4) or "5432"
                db_name = db_match.group(5)
                
                # Backup database
                db_backup_file = os.path.join(backup_dir, f"db_{timestamp}.sql")
                log_info(f"Backing up database to {db_backup_file}...")
                
                cmd = f"PGPASSWORD={db_password} pg_dump -h {db_host} -p {db_port} -U {db_user} -d {db_name} > {db_backup_file}"
                success, output = run_command(cmd, shell=True)
                
                if success:
                    log_info("Database backup successful.")
                else:
                    log_error(f"Database backup failed: {output}")
            else:
                log_error("Không thể phân tích DATABASE_URL từ file .env")
        else:
            log_error("Không tìm thấy DATABASE_URL trong file .env")
    else:
        log_error(f"Không tìm thấy file .env tại {env_file}")
    
    # Backup code và cấu hình
    log_info("Đang backup code và cấu hình...")
    cmd = f"tar -czf {backup_file} -C {APP_DIR} .env create_admin.py requirements.txt mik/ templates/ static/ 2>/dev/null"
    run_command(cmd, shell=True)
    
    if db_backup_file and os.path.isfile(db_backup_file):
        cmd = f"tar -rf {backup_file} {db_backup_file}"
        run_command(cmd, shell=True)
        os.remove(db_backup_file)
    
    log_info(f"Backup hoàn tất: {backup_file}")
    
    # Xóa các bản backup cũ (giữ lại 5 bản mới nhất)
    log_info("Dọn dẹp các bản backup cũ...")
    cmd = f"find {backup_dir} -name \"mikmon_backup_*.tar.gz\" -type f -printf '%T@ %p\\n' | sort -n | head -n -5 | cut -d' ' -f2- | xargs -r rm"
    run_command(cmd, shell=True)
    
    log_info("Quá trình backup đã hoàn tất.")
    return True

def create_bug_fix_script():
    """Tạo script khắc phục lỗi"""
    print_header("Tạo Script Khắc Phục Lỗi")
    
    log_info("Đang tạo script khắc phục lỗi tự động...")
    
    debug_script = os.path.join(APP_DIR, "debug_fix.py")
    content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

\"\"\"
Script tự động khắc phục lỗi và debugging cho MikroTik Monitor
\"\"\"

import os
import sys
import re
import time
import datetime
import traceback
import argparse
import logging
import json
import subprocess
from pathlib import Path

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("debug_fix")

class Debugger:
    def __init__(self, app_dir, service_name):
        self.app_dir = app_dir
        self.service_name = service_name
        self.venv_dir = os.path.join(app_dir, "venv")
        self.fixes_applied = []
        self.issues_detected = []
    
    def run_command(self, command, shell=False):
        \"\"\"Chạy lệnh shell và trả về kết quả\"\"\"
        try:
            if shell:
                process = subprocess.run(command, shell=True, check=True, 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                      text=True)
            else:
                process = subprocess.run(command.split(), check=True, 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                      text=True)
            return True, process.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def check_service_status(self):
        \"\"\"Kiểm tra trạng thái dịch vụ\"\"\"
        logger.info(f"Kiểm tra trạng thái dịch vụ {self.service_name}...")
        
        success, output = self.run_command(f"systemctl status {self.service_name}")
        if not success:
            self.issues_detected.append(f"Dịch vụ {self.service_name} không hoạt động")
            return False
        
        if "active (running)" not in output:
            self.issues_detected.append(f"Dịch vụ {self.service_name} không ở trạng thái chạy")
            return False
        
        logger.info(f"Dịch vụ {self.service_name} đang chạy bình thường.")
        return True
    
    def check_logs(self):
        \"\"\"Kiểm tra logs để tìm lỗi\"\"\"
        logger.info("Đang phân tích logs...")
        
        success, logs = self.run_command(f"journalctl -u {self.service_name} -n 100 --no-pager")
        if not success:
            logger.error(f"Không thể đọc logs: {logs}")
            return
        
        # Tìm các pattern lỗi phổ biến
        error_patterns = [
            (r"ImportError: No module named '([^']+)'", self.fix_missing_module),
            (r"SyntaxError: ([^\\n]+)", self.fix_syntax_error),
            (r"OperationalError: ([^\\n]+)", self.fix_db_error),
            (r"PermissionError: ([^\\n]+)", self.fix_permission_error),
            (r"ConnectionRefusedError: ([^\\n]+)", self.fix_connection_error),
            (r"FileNotFoundError: ([^\\n]+)", self.fix_missing_file),
        ]
        
        for pattern, fix_func in error_patterns:
            matches = re.findall(pattern, logs)
            for match in matches:
                self.issues_detected.append(f"Lỗi phát hiện: {match}")
                fix_func(match)
    
    def fix_missing_module(self, module_name):
        \"\"\"Sửa lỗi thiếu module\"\"\"
        logger.info(f"Đang khắc phục lỗi thiếu module: {module_name}")
        
        if not os.path.exists(self.venv_dir):
            logger.error(f"Không tìm thấy môi trường ảo tại {self.venv_dir}")
            return
        
        # Cài đặt module thiếu
        success, output = self.run_command(f"{self.venv_dir}/bin/pip install {module_name}")
        if success:
            logger.info(f"Đã cài đặt module {module_name}")
            self.fixes_applied.append(f"Đã cài đặt module thiếu: {module_name}")
        else:
            logger.error(f"Không thể cài đặt module {module_name}: {output}")
    
    def fix_syntax_error(self, error_info):
        \"\"\"Báo cáo lỗi cú pháp\"\"\"
        logger.info(f"Phát hiện lỗi cú pháp: {error_info}")
        
        # Tìm file có lỗi
        match = re.search(r"File \"([^\"]+)\", line (\d+)", error_info)
        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            
            # Đọc file để hiển thị đoạn code lỗi
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                start_line = max(0, line_num - 3)
                end_line = min(len(lines), line_num + 2)
                
                logger.info(f"Lỗi cú pháp trong file {file_path} dòng {line_num}:")
                for i in range(start_line, end_line):
                    prefix = ">>> " if i + 1 == line_num else "    "
                    logger.info(f"{prefix}{i + 1}: {lines[i].rstrip()}")
                
                self.fixes_applied.append(f"Đã xác định vị trí lỗi cú pháp tại {file_path} dòng {line_num}")
    
    def fix_db_error(self, error_info):
        \"\"\"Sửa lỗi cơ sở dữ liệu\"\"\"
        logger.info(f"Phát hiện lỗi cơ sở dữ liệu: {error_info}")
        
        # Kiểm tra dịch vụ PostgreSQL
        success, _ = self.run_command("systemctl is-active postgresql")
        if not success:
            logger.info("PostgreSQL không chạy, đang khởi động...")
            self.run_command("systemctl start postgresql")
            self.fixes_applied.append("Đã khởi động lại dịch vụ PostgreSQL")
        
        # Nếu lỗi liên quan đến bảng không tồn tại, có thể cần khởi tạo database
        if "relation" in error_info and "does not exist" in error_info:
            logger.info("Phát hiện lỗi bảng không tồn tại, đang thử khởi tạo database...")
            
            # Chạy migration hoặc khởi tạo database
            os.chdir(self.app_dir)
            success, output = self.run_command(f"{self.venv_dir}/bin/python create_admin.py")
            if success:
                logger.info("Đã khởi tạo database thành công")
                self.fixes_applied.append("Đã khởi tạo/cập nhật database")
            else:
                logger.error(f"Không thể khởi tạo database: {output}")
    
    def fix_permission_error(self, error_info):
        \"\"\"Sửa lỗi quyền truy cập\"\"\"
        logger.info(f"Phát hiện lỗi quyền truy cập: {error_info}")
        
        # Tìm đường dẫn file/thư mục bị lỗi quyền
        match = re.search(r"'([^']+)'", error_info)
        if match:
            path = match.group(1)
            
            if os.path.exists(path):
                # Kiểm tra xem đường dẫn có thuộc ứng dụng không
                if path.startswith(self.app_dir):
                    logger.info(f"Đang sửa quyền cho {path}...")
                    
                    if os.path.isdir(path):
                        self.run_command(f"chmod -R 755 {path}")
                    else:
                        self.run_command(f"chmod 644 {path}")
                    
                    # Đảm bảo owner đúng
                    self.run_command(f"chown -R mikmon:mikmon {path}")
                    
                    self.fixes_applied.append(f"Đã sửa quyền cho {path}")
                else:
                    logger.warning(f"Đường dẫn {path} không thuộc ứng dụng, không sửa quyền tự động")
    
    def fix_connection_error(self, error_info):
        \"\"\"Sửa lỗi kết nối\"\"\"
        logger.info(f"Phát hiện lỗi kết nối: {error_info}")
        
        # Nếu là lỗi kết nối đến PostgreSQL
        if "psycopg" in error_info or "postgresql" in error_info.lower():
            logger.info("Đang kiểm tra kết nối PostgreSQL...")
            
            # Kiểm tra dịch vụ PostgreSQL
            success, _ = self.run_command("systemctl is-active postgresql")
            if not success:
                logger.info("PostgreSQL không chạy, đang khởi động...")
                self.run_command("systemctl start postgresql")
                self.fixes_applied.append("Đã khởi động lại dịch vụ PostgreSQL do lỗi kết nối")
        
        # Nếu là lỗi kết nối đến Redis hoặc dịch vụ khác
        # Có thể thêm xử lý tương tự
    
    def fix_missing_file(self, error_info):
        \"\"\"Sửa lỗi thiếu file\"\"\"
        logger.info(f"Phát hiện lỗi thiếu file: {error_info}")
        
        # Tìm đường dẫn file bị thiếu
        match = re.search(r"'([^']+)'", error_info)
        if match:
            missing_file = match.group(1)
            
            # Kiểm tra một số trường hợp đặc biệt
            if missing_file.endswith(".env"):
                logger.info("Đang tạo file .env...")
                
                env_template = {
                    "FLASK_APP": "main.py",
                    "FLASK_ENV": "production",
                    "FLASK_DEBUG": "0",
                    "SECRET_KEY": self.generate_random_key(24),
                    "JWT_SECRET_KEY": self.generate_random_key(24),
                    "WTF_CSRF_SECRET_KEY": self.generate_random_key(24),
                    "DATABASE_URL": "postgresql://mikmon:mikmon_password@localhost:5432/mikmon"
                }
                
                with open(os.path.join(self.app_dir, ".env"), "w") as f:
                    for key, value in env_template.items():
                        f.write(f"{key}={value}\\n")
                
                self.fixes_applied.append("Đã tạo file .env từ template")
            else:
                # Báo cáo nhưng không tự tạo các file khác
                logger.warning(f"File thiếu: {missing_file} - cần tạo thủ công")
    
    def generate_random_key(self, length=24):
        \"\"\"Tạo key ngẫu nhiên\"\"\"
        import random
        import string
        chars = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
        return ''.join(random.choice(chars) for _ in range(length))
    
    def check_database(self):
        \"\"\"Kiểm tra cơ sở dữ liệu\"\"\"
        logger.info("Đang kiểm tra cơ sở dữ liệu...")
        
        # Đọc thông tin database từ .env
        env_file = os.path.join(self.app_dir, ".env")
        if not os.path.isfile(env_file):
            logger.error(f"Không tìm thấy file .env tại {env_file}")
            return
        
        db_url = None
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    db_url = line.strip().split("=", 1)[1]
                    break
        
        if not db_url:
            logger.error("Không tìm thấy DATABASE_URL trong file .env")
            return
        
        # Phân tích DATABASE_URL
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:/]+):?([0-9]*)/([^?]+)', db_url)
        if not match:
            logger.error(f"Không thể phân tích DATABASE_URL: {db_url}")
            return
        
        db_user = match.group(1)
        db_password = match.group(2)
        db_host = match.group(3)
        db_port = match.group(4) or "5432"
        db_name = match.group(5)
        
        # Kiểm tra PostgreSQL
        success, _ = self.run_command("systemctl is-active postgresql")
        if not success:
            logger.error("PostgreSQL không chạy")
            self.issues_detected.append("PostgreSQL không chạy")
            return
        
        # Kiểm tra kết nối đến database
        cmd = f"PGPASSWORD={db_password} psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -c 'SELECT 1'"
        success, output = self.run_command(cmd, shell=True)
        
        if not success:
            logger.error(f"Không thể kết nối đến database: {output}")
            self.issues_detected.append(f"Không thể kết nối đến database {db_name}")
        else:
            logger.info(f"Kết nối đến database {db_name} thành công")
    
    def check_and_fix_issues(self):
        \"\"\"Kiểm tra và sửa lỗi\"\"\"
        
        # Kiểm tra dịch vụ
        self.check_service_status()
        
        # Kiểm tra logs
        self.check_logs()
        
        # Kiểm tra database
        self.check_database()
        
        # Hiển thị kết quả
        if self.issues_detected:
            logger.info("\\nCác vấn đề đã phát hiện:")
            for issue in self.issues_detected:
                logger.info(f"  - {issue}")
        else:
            logger.info("\\nKhông phát hiện vấn đề nào.")
        
        if self.fixes_applied:
            logger.info("\\nCác sửa chữa đã áp dụng:")
            for fix in self.fixes_applied:
                logger.info(f"  - {fix}")
        else:
            logger.info("\\nKhông có sửa chữa nào được áp dụng.")
        
        # Khởi động lại dịch vụ nếu đã áp dụng sửa chữa
        if self.fixes_applied:
            logger.info("\\nĐang khởi động lại dịch vụ...")
            self.run_command(f"systemctl restart {self.service_name}")
            logger.info(f"Đã khởi động lại dịch vụ {self.service_name}")

def main():
    parser = argparse.ArgumentParser(description="Tự động khắc phục lỗi và debugging cho MikroTik Monitor")
    parser.add_argument("--app-dir", default="/opt/mikrotik-monitor", help="Thư mục cài đặt ứng dụng")
    parser.add_argument("--service", default="mikrotik-monitor", help="Tên dịch vụ")
    parser.add_argument("--verbose", action="store_true", help="Hiển thị chi tiết")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Kiểm tra quyền root
    if os.geteuid() != 0:
        logger.error("Script này cần chạy với quyền root. Vui lòng sử dụng sudo.")
        sys.exit(1)
    
    debugger = Debugger(args.app_dir, args.service)
    debugger.check_and_fix_issues()

if __name__ == "__main__":
    main()
"""
    
    with open(debug_script, 'w') as f:
        f.write(content)
    
    os.chmod(debug_script, 0o755)
    
    log_info(f"Đã tạo script khắc phục lỗi tại {debug_script}")
    log_info("Sử dụng lệnh sau để chạy script: sudo python debug_fix.py")
    
    return True

def show_menu():
    """Hiển thị menu và xử lý lựa chọn"""
    while True:
        print_header("MikroTik Monitor - Công Cụ Mở Rộng & Bảo Trì")
        
        # Hiển thị thông tin phiên bản
        git_dir = os.path.join(APP_DIR, ".git", "HEAD")
        if os.path.isfile(git_dir):
            os.chdir(APP_DIR)
            success, branch = run_command("git rev-parse --abbrev-ref HEAD")
            success, commit = run_command("git rev-parse --short HEAD")
            if success:
                print(f"Version: {Colors.BOLD}{branch.strip()}@{commit.strip()}{Colors.NC}")
        
        # Kiểm tra trạng thái dịch vụ
        success, status = run_command(f"systemctl is-active {SERVICE_NAME}")
        if success and "active" in status:
            print(f"Dịch vụ: {Colors.GREEN}Active{Colors.NC}")
        else:
            print(f"Dịch vụ: {Colors.RED}Inactive{Colors.NC}")
        
        print(f"Cổng: {DEFAULT_PORT}")
        print(f"Thư mục: {APP_DIR}")
        print()
        
        print(f"Chọn một tùy chọn:")
        print(f"  {Colors.BOLD}1.{Colors.NC} Kiểm tra và sửa chữa cài đặt")
        print(f"  {Colors.BOLD}2.{Colors.NC} Thêm module mới")
        print(f"  {Colors.BOLD}3.{Colors.NC} Cập nhật code từ repository")
        print(f"  {Colors.BOLD}4.{Colors.NC} Backup dữ liệu")
        print(f"  {Colors.BOLD}5.{Colors.NC} Thay đổi cổng")
        print(f"  {Colors.BOLD}6.{Colors.NC} Xem logs")
        print(f"  {Colors.BOLD}7.{Colors.NC} Tạo script khắc phục lỗi")
        print(f"  {Colors.BOLD}q.{Colors.NC} Thoát")
        print()
        
        choice = input("Nhập lựa chọn của bạn: ")
        
        if choice == '1':
            check_installation()
            check_port()
            check_and_fix_database()
        elif choice == '2':
            add_module()
        elif choice == '3':
            update_code()
        elif choice == '4':
            backup_data()
        elif choice == '5':
            new_port = input("Nhập cổng mới: ")
            update_port(new_port)
        elif choice == '6':
            success, logs = run_command(f"journalctl -u {SERVICE_NAME} -n 100 --no-pager")
            if success:
                print(logs)
            else:
                log_error(f"Không thể xem logs: {logs}")
        elif choice == '7':
            create_bug_fix_script()
        elif choice.lower() == 'q':
            print("Thoát chương trình.")
            sys.exit(0)
        else:
            log_error("Lựa chọn không hợp lệ.")
        
        # Đợi người dùng trước khi hiển thị lại menu
        input("\nNhấn Enter để tiếp tục...")

def main():
    """Hàm chính"""
    parser = argparse.ArgumentParser(description="Công cụ mở rộng và bảo trì MikroTik Monitor")
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra cài đặt")
    parser.add_argument("--add-module", help="Thêm module mới với tên chỉ định")
    parser.add_argument("--backup", action="store_true", help="Backup dữ liệu")
    parser.add_argument("--update", action="store_true", help="Cập nhật code từ repository")
    parser.add_argument("--port", type=int, help="Thay đổi cổng dịch vụ")
    parser.add_argument("--fix", action="store_true", help="Tạo script khắc phục lỗi")
    
    args = parser.parse_args()
    
    # Kiểm tra quyền root
    check_root()
    
    # Xử lý các lệnh đơn
    if args.check:
        check_installation()
        check_port()
        check_and_fix_database()
        return
    
    if args.add_module:
        add_module(args.add_module)
        return
    
    if args.backup:
        backup_data()
        return
    
    if args.update:
        update_code()
        return
    
    if args.port:
        update_port(str(args.port))
        return
    
    if args.fix:
        create_bug_fix_script()
        return
    
    # Nếu không có lệnh đơn, hiển thị menu
    show_menu()

if __name__ == "__main__":
    main()