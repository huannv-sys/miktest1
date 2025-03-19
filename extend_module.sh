#!/bin/bash

# Xác định màu sắc ANSI
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Đường dẫn cài đặt mặc định
APP_DIR="/opt/mikrotik-monitor"
VENV_DIR="${APP_DIR}/venv"
SERVICE_NAME="mikrotik-monitor"
DEFAULT_PORT="5050"

# Hàm hỗ trợ
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

print_header() {
    echo -e "\n${BOLD}$1${NC}\n"
}

# Kiểm tra quyền root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "Script này cần chạy với quyền root. Vui lòng sử dụng sudo."
        exit 1
    fi
}

# Kiểm tra cài đặt
check_installation() {
    if [ ! -d "$APP_DIR" ]; then
        log_error "Không tìm thấy thư mục cài đặt tại ${APP_DIR}."
        log_error "Vui lòng chạy script cài đặt trước."
        exit 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        log_warn "Không tìm thấy môi trường ảo Python tại ${VENV_DIR}."
        log_info "Đang tạo môi trường ảo mới..."
        python3 -m venv ${VENV_DIR}
        ${VENV_DIR}/bin/pip install --upgrade pip
    fi

    # Kiểm tra dịch vụ
    if ! systemctl is-active --quiet ${SERVICE_NAME}; then
        log_warn "Dịch vụ ${SERVICE_NAME} không chạy."
        read -p "Bạn có muốn khởi động dịch vụ không? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            systemctl start ${SERVICE_NAME}
            log_info "Đã khởi động dịch vụ ${SERVICE_NAME}."
        fi
    fi

    log_info "Kiểm tra cài đặt hoàn tất."
}

# Kiểm tra cổng
check_port() {
    if lsof -Pi :${DEFAULT_PORT} -sTCP:LISTEN -t >/dev/null ; then
        local pid=$(lsof -Pi :${DEFAULT_PORT} -sTCP:LISTEN -t)
        local process_name=$(ps -p $pid -o comm=)
        
        if [[ "$process_name" != *"python"* && "$process_name" != *"gunicorn"* ]]; then
            log_warn "Cổng ${DEFAULT_PORT} đang được sử dụng bởi tiến trình khác: $process_name (PID: $pid)."
            read -p "Bạn có muốn thay đổi cổng? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                read -p "Nhập cổng mới: " new_port
                update_port "$new_port"
            else
                log_warn "Tiếp tục với cổng ${DEFAULT_PORT}. Có thể gây xung đột!"
            fi
        else
            log_info "Cổng ${DEFAULT_PORT} đang được sử dụng bởi ứng dụng MikroTik Monitor."
        fi
    else
        log_info "Cổng ${DEFAULT_PORT} sẵn sàng để sử dụng."
    fi
}

# Cập nhật cổng
update_port() {
    local new_port=$1
    log_info "Đang cập nhật cổng từ ${DEFAULT_PORT} sang ${new_port}..."
    
    # Cập nhật cấu hình systemd
    if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
        sed -i "s/--bind 0.0.0.0:${DEFAULT_PORT}/--bind 0.0.0.0:${new_port}/g" /etc/systemd/system/${SERVICE_NAME}.service
        systemctl daemon-reload
    fi
    
    # Cập nhật cấu hình Nginx
    if [ -f "/etc/nginx/sites-available/${SERVICE_NAME}" ]; then
        sed -i "s/proxy_pass http:\/\/127.0.0.1:${DEFAULT_PORT};/proxy_pass http:\/\/127.0.0.1:${new_port};/g" /etc/nginx/sites-available/${SERVICE_NAME}
        systemctl reload nginx
    fi
    
    # Cập nhật biến toàn cục
    DEFAULT_PORT=${new_port}
    
    log_info "Đã cập nhật cổng. Đang khởi động lại dịch vụ..."
    systemctl restart ${SERVICE_NAME}
    log_info "Hoàn tất cập nhật cổng."
}

# Kiểm tra và sửa chữa PostgreSQL
check_and_fix_database() {
    log_info "Đang kiểm tra cơ sở dữ liệu PostgreSQL..."
    
    # Kiểm tra dịch vụ PostgreSQL
    if ! systemctl is-active --quiet postgresql; then
        log_warn "Dịch vụ PostgreSQL không chạy."
        log_info "Đang khởi động PostgreSQL..."
        systemctl start postgresql
    fi
    
    # Đọc thông tin cơ sở dữ liệu từ .env
    if [ -f "${APP_DIR}/.env" ]; then
        source <(grep DATABASE_URL "${APP_DIR}/.env")
        
        # Phân tích DATABASE_URL để lấy thông tin
        if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:/]+):?([0-9]*)/([^?]+) ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASSWORD="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]:-5432}"
            DB_NAME="${BASH_REMATCH[5]}"
            
            # Kiểm tra kết nối đến PostgreSQL
            if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw ${DB_NAME}; then
                log_warn "Không tìm thấy cơ sở dữ liệu ${DB_NAME}."
                read -p "Bạn có muốn tạo cơ sở dữ liệu mới không? (y/n) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    log_info "Đang tạo cơ sở dữ liệu ${DB_NAME}..."
                    
                    # Tạo user nếu chưa tồn tại
                    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}';" | grep -q 1; then
                        sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
                    fi
                    
                    # Tạo database
                    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
                    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
                    
                    log_info "Đã tạo cơ sở dữ liệu ${DB_NAME} thành công."
                    
                    # Khởi tạo dữ liệu
                    log_info "Đang khởi tạo dữ liệu ban đầu..."
                    cd ${APP_DIR}
                    sudo -u ${APP_USER:-mikmon} ${VENV_DIR}/bin/python create_admin.py
                    log_info "Đã khởi tạo dữ liệu ban đầu."
                fi
            else
                log_info "Cơ sở dữ liệu ${DB_NAME} đã tồn tại."
            fi
        else
            log_error "Không thể phân tích DATABASE_URL từ file .env"
        fi
    else
        log_error "Không tìm thấy file .env tại ${APP_DIR}/.env"
    fi
}

# Cập nhật code từ git
update_code() {
    log_info "Đang cập nhật code từ repository..."
    
    # Kiểm tra xem có phải là repository git không
    if [ -d "${APP_DIR}/.git" ]; then
        cd ${APP_DIR}
        
        # Lưu các thay đổi cục bộ
        if [[ -n $(git status --porcelain) ]]; then
            log_warn "Phát hiện các thay đổi cục bộ."
            read -p "Bạn có muốn lưu các thay đổi cục bộ trước khi cập nhật không? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Đang tạo bản sao lưu thay đổi cục bộ..."
                timestamp=$(date +"%Y%m%d_%H%M%S")
                git diff > "${APP_DIR}/local_changes_${timestamp}.patch"
                log_info "Đã lưu thay đổi tại: ${APP_DIR}/local_changes_${timestamp}.patch"
            fi
        fi
        
        # Pull code mới
        log_info "Đang tải code mới từ repository..."
        git pull
        
        # Cập nhật dependencies
        log_info "Đang cập nhật dependencies..."
        ${VENV_DIR}/bin/pip install -r ${APP_DIR}/requirements.txt
        
        # Khởi động lại dịch vụ
        log_info "Đang khởi động lại dịch vụ..."
        systemctl restart ${SERVICE_NAME}
        
        log_info "Đã cập nhật code thành công."
    else
        log_error "Thư mục ${APP_DIR} không phải là một Git repository."
        log_info "Bạn cần cài đặt lại ứng dụng từ git repository."
    fi
}

# Thêm module mới
add_module() {
    print_header "Thêm Module Mới"
    
    read -p "Nhập tên module: " module_name
    module_name=$(echo "$module_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    
    if [ -z "$module_name" ]; then
        log_error "Tên module không được để trống."
        return 1
    fi
    
    # Tạo cấu trúc thư mục
    log_info "Đang tạo cấu trúc module ${module_name}..."
    
    MODULE_DIR="${APP_DIR}/mik/app/modules/${module_name}"
    mkdir -p "${MODULE_DIR}"
    mkdir -p "${MODULE_DIR}/templates"
    mkdir -p "${MODULE_DIR}/static/js"
    mkdir -p "${MODULE_DIR}/static/css"
    
    # Tạo các file cơ bản
    cat > "${MODULE_DIR}/__init__.py" << EOL
# Module: ${module_name}

from flask import Blueprint

${module_name}_bp = Blueprint('${module_name}', __name__, 
                        url_prefix='/${module_name}',
                        template_folder='templates', 
                        static_folder='static')

from . import routes
EOL

    cat > "${MODULE_DIR}/routes.py" << EOL
# Routes for ${module_name} module

from . import ${module_name}_bp
from flask import render_template, jsonify, request
from flask_login import login_required


@${module_name}_bp.route('/')
@login_required
def index():
    """Main view for ${module_name} module"""
    return render_template('${module_name}/index.html', title='${module_name}')


@${module_name}_bp.route('/api/data')
@login_required
def get_data():
    """API endpoint for ${module_name} data"""
    # TODO: Implement data retrieval logic
    return jsonify({
        'status': 'success',
        'data': []
    })
EOL

    mkdir -p "${MODULE_DIR}/templates/${module_name}"
    cat > "${MODULE_DIR}/templates/${module_name}/index.html" << EOL
{% extends "base.html" %}

{% block title %}${module_name}{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <h1>${module_name}</h1>
            <hr>
            <div class="card">
                <div class="card-header">
                    <h5>Tổng quan</h5>
                </div>
                <div class="card-body">
                    <div id="${module_name}-container">
                        <p>Nội dung module ${module_name} sẽ hiển thị ở đây.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('${module_name}.static', filename='js/${module_name}.js') }}"></script>
{% endblock %}
EOL

    cat > "${MODULE_DIR}/static/js/${module_name}.js" << EOL
/**
 * ${module_name} functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('${module_name} module initialized');
    
    // TODO: Implement module functionality
    
    // Example: Load data from API
    async function loadData() {
        try {
            const response = await fetch('/api/${module_name}/data');
            const data = await response.json();
            
            if (data.status === 'success') {
                console.log('Data loaded:', data);
                // TODO: Process and display data
            }
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }
    
    // Initialize module
    loadData();
});
EOL

    cat > "${MODULE_DIR}/static/css/${module_name}.css" << EOL
/* CSS styles for ${module_name} module */
#${module_name}-container {
    padding: 10px;
}
EOL

    # Cập nhật file __init__.py của ứng dụng để đăng ký module
    INIT_FILE="${APP_DIR}/mik/app/__init__.py"
    
    if [ -f "$INIT_FILE" ]; then
        # Kiểm tra xem đã import module chưa
        if ! grep -q "from mik.app.modules.${module_name} import ${module_name}_bp" "$INIT_FILE"; then
            # Thêm import và đăng ký blueprint
            if grep -q "def create_app" "$INIT_FILE"; then
                # Thêm vào sau dòng import cuối cùng
                sed -i "/from flask import Flask/a from mik.app.modules.${module_name} import ${module_name}_bp" "$INIT_FILE"
                
                # Thêm vào trong hàm create_app để đăng ký blueprint
                sed -i "/app = Flask/a \    app.register_blueprint(${module_name}_bp)" "$INIT_FILE"
            else
                log_warn "Không tìm thấy hàm create_app trong ${INIT_FILE}"
                log_info "Bạn cần thêm thủ công dòng sau vào nơi thích hợp:"
                echo "from mik.app.modules.${module_name} import ${module_name}_bp"
                echo "app.register_blueprint(${module_name}_bp)"
            fi
        fi
    else
        log_warn "Không tìm thấy file ${INIT_FILE}"
    fi
    
    # Cập nhật menu trong templates/base.html
    BASE_TEMPLATE="${APP_DIR}/templates/base.html"
    if [ -f "$BASE_TEMPLATE" ]; then
        # Tìm vị trí menu
        if grep -q "<li class=\"nav-item\">" "$BASE_TEMPLATE"; then
            # Tạo dòng menu mới
            MENU_ITEM="<li class=\"nav-item\"><a class=\"nav-link\" href=\"/${module_name}\"><i class=\"fas fa-puzzle-piece\"></i> ${module_name}</a></li>"
            
            # Thêm vào sau một menu item khác
            sed -i "/<li class=\"nav-item\">/a ${MENU_ITEM}" "$BASE_TEMPLATE"
        else
            log_warn "Không tìm thấy vị trí menu trong ${BASE_TEMPLATE}"
        fi
    else
        log_warn "Không tìm thấy file ${BASE_TEMPLATE}"
    fi
    
    log_info "Module ${module_name} đã được tạo thành công!"
    log_info "Đường dẫn: ${MODULE_DIR}"
    log_info "URL: http://localhost:${DEFAULT_PORT}/${module_name}"
    
    # Khởi động lại dịch vụ
    read -p "Bạn có muốn khởi động lại dịch vụ không? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Đang khởi động lại dịch vụ..."
        systemctl restart ${SERVICE_NAME}
        log_info "Đã khởi động lại dịch vụ thành công."
    fi
}

# Backup dữ liệu
backup_data() {
    print_header "Backup Dữ Liệu"
    
    BACKUP_DIR="${APP_DIR}/backups"
    timestamp=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="${BACKUP_DIR}/mikmon_backup_${timestamp}.tar.gz"
    
    # Tạo thư mục backup nếu chưa tồn tại
    mkdir -p ${BACKUP_DIR}
    
    log_info "Đang backup dữ liệu..."
    
    # Backup database
    log_info "Đang backup cơ sở dữ liệu..."
    
    if [ -f "${APP_DIR}/.env" ]; then
        source <(grep DATABASE_URL "${APP_DIR}/.env")
        
        # Phân tích DATABASE_URL để lấy thông tin
        if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:/]+):?([0-9]*)/([^?]+) ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASSWORD="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]:-5432}"
            DB_NAME="${BASH_REMATCH[5]}"
            
            # Backup database
            DB_BACKUP_FILE="${BACKUP_DIR}/db_${timestamp}.sql"
            log_info "Backing up database to ${DB_BACKUP_FILE}..."
            
            PGPASSWORD="${DB_PASSWORD}" pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} > ${DB_BACKUP_FILE}
            
            if [ $? -eq 0 ]; then
                log_info "Database backup successful."
            else
                log_error "Database backup failed."
            fi
        else
            log_error "Không thể phân tích DATABASE_URL từ file .env"
        fi
    else
        log_error "Không tìm thấy file .env tại ${APP_DIR}/.env"
    fi
    
    # Backup code và cấu hình
    log_info "Đang backup code và cấu hình..."
    tar -czf ${BACKUP_FILE} -C ${APP_DIR} .env create_admin.py requirements.txt mik/ templates/ static/ 2>/dev/null
    
    if [ -f "${DB_BACKUP_FILE}" ]; then
        tar -rf ${BACKUP_FILE} ${DB_BACKUP_FILE}
        rm ${DB_BACKUP_FILE}
    fi
    
    log_info "Backup hoàn tất: ${BACKUP_FILE}"
    
    # Xóa các bản backup cũ (giữ lại 5 bản mới nhất)
    log_info "Dọn dẹp các bản backup cũ..."
    find ${BACKUP_DIR} -name "mikmon_backup_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | head -n -5 | cut -d' ' -f2- | xargs -r rm
    
    log_info "Quá trình backup đã hoàn tất."
}

# Hiển thị thông tin và menu
show_menu() {
    print_header "MikroTik Monitor - Công Cụ Mở Rộng & Bảo Trì"
    
    # Hiển thị thông tin phiên bản
    if [ -f "${APP_DIR}/.git/HEAD" ]; then
        GIT_BRANCH=$(cd ${APP_DIR} && git rev-parse --abbrev-ref HEAD)
        GIT_COMMIT=$(cd ${APP_DIR} && git rev-parse --short HEAD)
        echo -e "Version: ${BOLD}${GIT_BRANCH}@${GIT_COMMIT}${NC}"
    fi
    
    # Kiểm tra trạng thái dịch vụ
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo -e "Dịch vụ: ${GREEN}Active${NC}"
    else
        echo -e "Dịch vụ: ${RED}Inactive${NC}"
    fi
    
    echo -e "Cổng: ${DEFAULT_PORT}"
    echo -e "Thư mục: ${APP_DIR}"
    echo
    
    echo -e "Chọn một tùy chọn:"
    echo -e "  ${BOLD}1.${NC} Kiểm tra và sửa chữa cài đặt"
    echo -e "  ${BOLD}2.${NC} Thêm module mới"
    echo -e "  ${BOLD}3.${NC} Cập nhật code từ repository"
    echo -e "  ${BOLD}4.${NC} Backup dữ liệu"
    echo -e "  ${BOLD}5.${NC} Thay đổi cổng"
    echo -e "  ${BOLD}6.${NC} Xem logs"
    echo -e "  ${BOLD}q.${NC} Thoát"
    echo
    
    read -p "Nhập lựa chọn của bạn: " choice
    
    case $choice in
        1)
            check_installation
            check_port
            check_and_fix_database
            ;;
        2)
            add_module
            ;;
        3)
            update_code
            ;;
        4)
            backup_data
            ;;
        5)
            read -p "Nhập cổng mới: " new_port
            update_port "$new_port"
            ;;
        6)
            journalctl -u ${SERVICE_NAME} -n 100 --no-pager
            ;;
        q|Q)
            echo "Thoát chương trình."
            exit 0
            ;;
        *)
            log_error "Lựa chọn không hợp lệ."
            ;;
    esac
    
    # Quay lại menu
    read -p "Nhấn Enter để tiếp tục..." dummy
    show_menu
}

# Main function
main() {
    # Kiểm tra quyền root
    check_root
    
    # Hiển thị menu
    show_menu
}

# Run the main function
main