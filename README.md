# MikroTik Monitor

Dashboard giám sát và quản lý thiết bị MikroTik toàn diện, hỗ trợ cài đặt tự động trên Ubuntu 24.04 và Windows.

## Tính năng

- Giám sát tình trạng thiết bị theo thời gian thực
- Theo dõi hiệu suất CPU, bộ nhớ và mạng
- Quản lý danh sách các thiết bị MikroTik
- Hiển thị bản đồ mạng và kết nối giữa các thiết bị
- Cảnh báo khi phát hiện sự cố hoặc khi thông số vượt ngưỡng
- Giám sát kết nối VPN
- Hỗ trợ triển khai linh hoạt (Baremetal, Docker)

## Cài đặt tự động

Chúng tôi cung cấp các script cài đặt tự động cho các nền tảng phổ biến.

### Phương thức 1: Script cài đặt tự động

Sử dụng script cài đặt thông minh sẽ tự động phát hiện hệ điều hành và chọn phương thức cài đặt phù hợp:

```bash
./install.sh
```

### Phương thức 2: Script cài đặt trực tiếp

#### Ubuntu 24.04

```bash
sudo ./install_ubuntu_24.04.sh
```

#### Windows (PowerShell với quyền Administrator)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install_windows.ps1
```

### Phương thức 3: Sử dụng Docker

```bash
docker-compose up -d
```

### Phương thức 4: Cài đặt thủ công

Xem hướng dẫn chi tiết trong file [INSTALLATION.md](INSTALLATION.md)

## Yêu cầu hệ thống

### Ubuntu 24.04
- Python 3.11 hoặc cao hơn
- PostgreSQL 14 hoặc cao hơn
- Nginx (Tùy chọn nếu muốn reverse proxy)

### Windows
- Windows 10/11 hoặc Windows Server 2019/2022
- Python 3.11 hoặc cao hơn
- PostgreSQL 14 hoặc cao hơn

### Docker
- Docker Engine 20.10+
- Docker Compose v2+

## Cấu hình môi trường

Tệp `.env` sẽ được tạo tự động trong quá trình cài đặt. Nếu bạn cài đặt thủ công, hãy tạo file `.env` với nội dung mẫu sau:

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
DATABASE_URL=postgresql://username:password@localhost:5432/dbname

# MikroTik Connection Settings
MIKROTIK_CONNECTION_TIMEOUT=10
MIKROTIK_COMMAND_TIMEOUT=15
```

## Thông tin đăng nhập mặc định

Sau khi cài đặt, bạn có thể đăng nhập với thông tin mặc định:

- Username: `admin`
- Password: `admin123`

**Lưu ý quan trọng**: Vui lòng thay đổi mật khẩu mặc định ngay sau khi đăng nhập lần đầu tiên.

## Cấu trúc dự án

```
mikrotik-monitor/
├── mik/                # Package chính
│   ├── app/            # Ứng dụng Flask
│   │   ├── api/        # API endpoints
│   │   ├── core/       # Logic nghiệp vụ
│   │   ├── database/   # Mô hình và CRUD 
│   │   ├── static/     # Tài nguyên tĩnh
│   │   └── templates/  # Templates
├── templates/          # Templates giao diện
│   ├── base.html       # Template cơ sở
│   ├── index.html      # Trang chủ
│   ├── login.html      # Trang đăng nhập
│   └── dashboard.html  # Dashboard chính
├── dependencies.txt    # Danh sách gói phụ thuộc
├── Dockerfile          # File cấu hình Docker
├── docker-compose.yml  # Cấu hình Docker Compose
├── install.sh          # Script cài đặt thông minh
├── install_ubuntu_24.04.sh # Script cài đặt cho Ubuntu 24.04
├── install_windows.ps1 # Script cài đặt cho Windows
├── INSTALLATION.md     # Hướng dẫn cài đặt chi tiết
├── run_server.py       # Entry point chính
└── run.py              # Entry point thay thế
```

## Quản lý dịch vụ sau khi cài đặt

### Ubuntu 24.04
```bash
# Khởi động dịch vụ
sudo systemctl start mikrotik-monitor

# Dừng dịch vụ
sudo systemctl stop mikrotik-monitor

# Khởi động lại dịch vụ
sudo systemctl restart mikrotik-monitor

# Kiểm tra trạng thái
sudo systemctl status mikrotik-monitor

# Xem logs
sudo journalctl -u mikrotik-monitor
```

### Windows
```powershell
# Khởi động dịch vụ
Start-Service MikroTikMonitor

# Dừng dịch vụ
Stop-Service MikroTikMonitor

# Khởi động lại dịch vụ
Restart-Service MikroTikMonitor

# Kiểm tra trạng thái
Get-Service MikroTikMonitor
```

### Docker
```bash
# Khởi động
docker-compose up -d

# Dừng và xóa container
docker-compose down

# Xem logs
docker-compose logs -f

# Khởi động lại
docker-compose restart
```"# miktest1" 
