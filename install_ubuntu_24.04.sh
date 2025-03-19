#!/bin/bash
# Mikrotik Monitor - Ubuntu 24.04 Installation Script
# This script installs all requirements and sets up the MikroTik Monitor application

set -e

# ANSI Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Variables
APP_NAME="MikroTik Monitor"
APP_DIR="/opt/mikrotik-monitor"
APP_USER="mikmon"
PYTHON_VERSION="3.11"
VENV_DIR="${APP_DIR}/venv"
DEFAULT_PORT="5050"
SERVICE_NAME="mikrotik-monitor"
POSTGRES_DB="mikmon"
POSTGRES_USER="mikmon"
POSTGRES_PASSWORD=$(openssl rand -base64 12)
SECRET_KEY=$(openssl rand -base64 24)
JWT_SECRET_KEY=$(openssl rand -base64 24)
WTF_CSRF_SECRET_KEY=$(openssl rand -base64 24)

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BOLD}$1${NC}\n"
}

install_dependencies() {
    print_header "Installing system dependencies"
    
    log_info "Updating package lists..."
    apt-get update
    
    log_info "Installing required packages..."
    apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-dev python${PYTHON_VERSION}-venv \
                       postgresql postgresql-contrib libpq-dev build-essential \
                       libffi-dev libssl-dev git nginx curl sudo unzip

    log_info "Installing pip..."
    apt-get install -y python3-pip
    
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        log_error "Python ${PYTHON_VERSION} installation failed."
        exit 1
    fi
    
    log_info "System dependencies installed successfully."
}

create_user() {
    print_header "Creating application user"
    
    if id "${APP_USER}" &>/dev/null; then
        log_warn "User ${APP_USER} already exists."
    else
        log_info "Creating user ${APP_USER}..."
        useradd -m -s /bin/bash -d /home/${APP_USER} ${APP_USER}
        log_info "User created successfully."
    fi
}

setup_postgresql() {
    print_header "Setting up PostgreSQL database"
    
    log_info "Ensuring PostgreSQL is running..."
    systemctl enable postgresql
    systemctl start postgresql
    
    log_info "Creating database user and database..."
    # Check if database user exists
    if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}';" | grep -q 1; then
        log_warn "Database user ${POSTGRES_USER} already exists."
    else
        sudo -u postgres psql -c "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"
        log_info "Database user created."
    fi
    
    # Check if database exists
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw ${POSTGRES_DB}; then
        log_warn "Database ${POSTGRES_DB} already exists."
    else
        sudo -u postgres psql -c "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};"
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};"
        log_info "Database created."
    fi
    
    log_info "PostgreSQL setup completed."
}

setup_application() {
    print_header "Setting up MikroTik Monitor application"
    
    log_info "Creating application directory..."
    mkdir -p ${APP_DIR}
    
    if [ -d "${APP_DIR}/.git" ]; then
        log_info "Git repository already exists, pulling latest changes..."
        cd ${APP_DIR}
        git pull
    else
        log_info "Cloning application repository..."
        # Replace with your actual Git repository URL
        git clone https://github.com/yourusername/mikrotik-monitor.git ${APP_DIR}
    fi
    
    log_info "Creating Python virtual environment..."
    python${PYTHON_VERSION} -m venv ${VENV_DIR}
    
    log_info "Installing Python dependencies..."
    ${VENV_DIR}/bin/pip install --upgrade pip
    ${VENV_DIR}/bin/pip install wheel
    ${VENV_DIR}/bin/pip install -r ${APP_DIR}/requirements.txt
    
    log_info "Setting up environment configuration..."
    cat > ${APP_DIR}/.env << EOL
# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=production
FLASK_DEBUG=0

# Security Keys
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
WTF_CSRF_SECRET_KEY=${WTF_CSRF_SECRET_KEY}

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_COOKIE_SECURE=1
JWT_COOKIE_CSRF_PROTECT=1

# Database Configuration
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}

# MikroTik Connection Settings
MIKROTIK_CONNECTION_TIMEOUT=10
MIKROTIK_COMMAND_TIMEOUT=15
MIKROTIK_BACKUP_TIMEOUT=60
MIKROTIK_RESTORE_TIMEOUT=120
EOL
    
    log_info "Setting permissions..."
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
    chmod -R 750 ${APP_DIR}
    chmod 640 ${APP_DIR}/.env
    
    log_info "Application setup completed."
}

setup_systemd_service() {
    print_header "Setting up systemd service"
    
    log_info "Creating systemd service file..."
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOL
[Unit]
Description=MikroTik Monitor Web Application
After=network.target postgresql.service

[Service]
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/gunicorn --workers 3 --bind 0.0.0.0:${DEFAULT_PORT} app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOL
    
    log_info "Enabling and starting service..."
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    systemctl start ${SERVICE_NAME}
    
    log_info "Service setup completed."
}

setup_nginx() {
    print_header "Setting up Nginx as reverse proxy"
    
    log_info "Creating Nginx configuration file..."
    cat > /etc/nginx/sites-available/${SERVICE_NAME} << EOL
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:${DEFAULT_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias ${APP_DIR}/static;
        expires 30d;
    }
}
EOL
    
    log_info "Enabling Nginx site..."
    ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/
    
    # Remove default Nginx site if it exists
    if [ -f /etc/nginx/sites-enabled/default ]; then
        log_info "Removing default Nginx site..."
        rm -f /etc/nginx/sites-enabled/default
    fi
    
    log_info "Testing Nginx configuration..."
    nginx -t
    
    log_info "Restarting Nginx..."
    systemctl restart nginx
    
    log_info "Nginx setup completed."
}

create_admin_user() {
    print_header "Creating admin user"
    
    log_info "Creating initial admin user..."
    cd ${APP_DIR}
    sudo -u ${APP_USER} ${VENV_DIR}/bin/python create_admin.py
    
    log_info "Admin user created successfully."
}

generate_requirements_file() {
    print_header "Generating requirements.txt file"
    
    cat > ${APP_DIR}/requirements.txt << EOL
apscheduler>=3.11.0
cryptography==41.0.5
flask-socketio>=5.5.1
flask==3.0.0
flask-cors==4.0.0
flask-jwt-extended>=4.7.1
flask-login==0.6.3
flask-sqlalchemy==3.1.1
flask-wtf==1.2.1
gunicorn>=23.0.0
librouteros>=3.4.1
python-dotenv==1.0.0
sqlalchemy==2.0.23
werkzeug==3.0.1
wtforms>=3.2.1
netifaces>=0.11.0
psycopg2-binary>=2.9.10
requests>=2.32.3
pyjwt>=2.10.1
bcrypt>=4.3.0
sqlalchemy-utils>=0.41.2
flask-migrate>=4.1.0
EOL
    
    log_info "Requirements file generated."
}

show_completion_message() {
    print_header "Installation Completed!"
    
    echo -e "${GREEN}${BOLD}MikroTik Monitor has been successfully installed!${NC}"
    echo
    echo -e "Database Information:"
    echo -e "  ${BOLD}Database:${NC} ${POSTGRES_DB}"
    echo -e "  ${BOLD}Username:${NC} ${POSTGRES_USER}"
    echo -e "  ${BOLD}Password:${NC} ${POSTGRES_PASSWORD}"
    echo
    echo -e "Admin User Details:"
    echo -e "  ${BOLD}Username:${NC} admin"
    echo -e "  ${BOLD}Password:${NC} admin123 (PLEASE CHANGE IMMEDIATELY AFTER LOGIN)"
    echo
    echo -e "Access the application at: ${BOLD}http://YOUR_SERVER_IP${NC}"
    echo
    echo -e "${YELLOW}Please save these credentials in a secure location.${NC}"
    echo
    echo -e "For any issues, please check the logs:"
    echo -e "  ${BOLD}journalctl -u ${SERVICE_NAME}${NC}"
    echo
}

# Main installation process
main() {
    # Check if running as root
    if [ "$(id -u)" -ne 0 ]; then
        log_error "This script must be run as root. Please use sudo."
        exit 1
    fi
    
    print_header "Starting ${APP_NAME} installation on Ubuntu 24.04"
    
    # Execute installation steps
    install_dependencies
    create_user
    setup_postgresql
    generate_requirements_file
    setup_application
    setup_systemd_service
    setup_nginx
    create_admin_user
    
    show_completion_message
}

# Run the main function
main