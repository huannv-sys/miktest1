# Hướng dẫn cài đặt MikroTik Monitor

## Yêu cầu hệ thống

### Ubuntu 24.04
- Python 3.11 hoặc cao hơn
- PostgreSQL 14 hoặc cao hơn 
- Nginx (Tùy chọn nếu muốn reverse proxy)
- Git

### Windows
- Windows 10/11 hoặc Windows Server 2019/2022
- Python 3.11 hoặc cao hơn
- PostgreSQL 14 hoặc cao hơn

## Cài đặt tự động

### Ubuntu 24.04

1. Tải script cài đặt:
```bash
wget https://raw.githubusercontent.com/yourusername/mikrotik-monitor/main/install_ubuntu_24.04.sh
```

2. Cấp quyền thực thi cho script:
```bash
chmod +x install_ubuntu_24.04.sh
```

3. Chạy script với quyền root:
```bash
sudo ./install_ubuntu_24.04.sh
```

4. Sau khi cài đặt hoàn tất, truy cập ứng dụng qua trình duyệt web:
```
http://your-server-ip
```

### Windows

1. Mở PowerShell với quyền Administrator

2. Tải script cài đặt:
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/yourusername/mikrotik-monitor/main/install_windows.ps1" -OutFile "install_windows.ps1"
```

3. Cho phép thực thi script:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

4. Chạy script:
```powershell
.\install_windows.ps1
```

5. Sau khi cài đặt hoàn tất, truy cập ứng dụng qua trình duyệt web:
```
http://localhost:5000
```

## Cài đặt thủ công

### Ubuntu 24.04

1. Cài đặt các gói phụ thuộc:
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-dev python3.11-venv postgresql postgresql-contrib libpq-dev build-essential libffi-dev libssl-dev git nginx
```

2. Tạo và cấu hình cơ sở dữ liệu PostgreSQL:
```bash
sudo -u postgres psql -c "CREATE USER mikmon WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE mikmon OWNER mikmon;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mikmon TO mikmon;"
```

3. Tạo thư mục ứng dụng:
```bash
sudo mkdir -p /opt/mikrotik-monitor
cd /opt/mikrotik-monitor
```

4. Tải mã nguồn ứng dụng:
```bash
sudo git clone https://github.com/yourusername/mikrotik-monitor.git .
```

5. Tạo môi trường ảo Python:
```bash
sudo python3.11 -m venv venv
sudo venv/bin/pip install --upgrade pip wheel
sudo venv/bin/pip install -r dependencies.txt
```

6. Tạo file cấu hình môi trường `.env`:
```bash
sudo cat > .env << EOL
# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=production
FLASK_DEBUG=0

# Security Keys
SECRET_KEY=$(openssl rand -base64 24)
JWT_SECRET_KEY=$(openssl rand -base64 24)
WTF_CSRF_SECRET_KEY=$(openssl rand -base64 24)

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_COOKIE_SECURE=1
JWT_COOKIE_CSRF_PROTECT=1

# Database Configuration
DATABASE_URL=postgresql://mikmon:your_password@localhost:5432/mikmon

# MikroTik Connection Settings
MIKROTIK_CONNECTION_TIMEOUT=10
MIKROTIK_COMMAND_TIMEOUT=15
MIKROTIK_BACKUP_TIMEOUT=60
MIKROTIK_RESTORE_TIMEOUT=120
EOL
```

7. Tạo người dùng admin mặc định:
```bash
sudo venv/bin/python create_admin.py
```

8. Tạo service systemd:
```bash
sudo cat > /etc/systemd/system/mikrotik-monitor.service << EOL
[Unit]
Description=MikroTik Monitor Web Application
After=network.target postgresql.service

[Service]
WorkingDirectory=/opt/mikrotik-monitor
Environment="PATH=/opt/mikrotik-monitor/venv/bin"
ExecStart=/opt/mikrotik-monitor/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mikrotik-monitor

[Install]
WantedBy=multi-user.target
EOL
```

9. Kích hoạt và khởi động service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mikrotik-monitor
sudo systemctl start mikrotik-monitor
```

10. Cấu hình Nginx (tùy chọn):
```bash
sudo cat > /etc/nginx/sites-available/mikrotik-monitor << EOL
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias /opt/mikrotik-monitor/static;
        expires 30d;
    }
}
EOL

sudo ln -sf /etc/nginx/sites-available/mikrotik-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Windows

1. Cài đặt Python 3.11 từ [python.org](https://www.python.org/downloads/)

2. Cài đặt PostgreSQL từ [postgresql.org](https://www.postgresql.org/download/windows/)

3. Tạo cơ sở dữ liệu và người dùng trong PostgreSQL:
   - Mở SQL Shell (psql)
   - Đăng nhập với tài khoản postgres
   - Chạy các lệnh sau:
   ```sql
   CREATE USER mikmon WITH PASSWORD 'your_password';
   CREATE DATABASE mikmon OWNER mikmon;
   GRANT ALL PRIVILEGES ON DATABASE mikmon TO mikmon;
   ```

4. Tạo thư mục ứng dụng:
```cmd
mkdir C:\MikroTikMonitor
cd C:\MikroTikMonitor
```

5. Tải xuống mã nguồn ứng dụng từ repository hoặc sao chép từ thư mục hiện tại

6. Tạo môi trường ảo Python:
```cmd
python -m venv venv
venv\Scripts\pip install --upgrade pip wheel
venv\Scripts\pip install -r dependencies.txt
```

7. Tạo file cấu hình `.env`:
```
# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=production
FLASK_DEBUG=0

# Security Keys
SECRET_KEY=your_random_secret_key
JWT_SECRET_KEY=your_random_jwt_key
WTF_CSRF_SECRET_KEY=your_random_csrf_key

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_COOKIE_SECURE=1
JWT_COOKIE_CSRF_PROTECT=1

# Database Configuration
DATABASE_URL=postgresql://mikmon:your_password@localhost:5432/mikmon

# MikroTik Connection Settings
MIKROTIK_CONNECTION_TIMEOUT=10
MIKROTIK_COMMAND_TIMEOUT=15
MIKROTIK_BACKUP_TIMEOUT=60
MIKROTIK_RESTORE_TIMEOUT=120
```

8. Tạo người dùng admin mặc định:
```cmd
venv\Scripts\python create_admin.py
```

9. Tạo file khởi động:
```cmd
echo @echo off > start_server.bat
echo cd /d %~dp0 >> start_server.bat
echo call venv\Scripts\activate.bat >> start_server.bat
echo python app.py >> start_server.bat
```

10. Tải và cài đặt NSSM (Non-Sucking Service Manager) từ [nssm.cc](https://nssm.cc/download)

11. Tạo Windows Service bằng NSSM:
```cmd
nssm install MikroTikMonitor "C:\MikroTikMonitor\start_server.bat"
nssm set MikroTikMonitor DisplayName "MikroTik Monitor"
nssm set MikroTikMonitor Description "MikroTik Monitor Web Application"
nssm set MikroTikMonitor AppDirectory "C:\MikroTikMonitor"
nssm set MikroTikMonitor AppStdout "C:\MikroTikMonitor\logs\service_stdout.log"
nssm set MikroTikMonitor AppStderr "C:\MikroTikMonitor\logs\service_stderr.log"
nssm start MikroTikMonitor
```

## Thông tin đăng nhập mặc định

Sau khi cài đặt, bạn có thể đăng nhập với thông tin mặc định:

- Username: `admin`
- Password: `admin123`

**Lưu ý quan trọng**: Vui lòng thay đổi mật khẩu mặc định ngay sau khi đăng nhập lần đầu tiên.