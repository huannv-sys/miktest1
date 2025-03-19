# MikroTik Monitor

Dashboard giám sát và quản lý thiết bị MikroTik toàn diện.

## Tính năng

- Giám sát tình trạng thiết bị theo thời gian thực
- Theo dõi hiệu suất CPU, bộ nhớ và mạng
- Quản lý danh sách các thiết bị MikroTik
- Hiển thị bản đồ mạng và kết nối giữa các thiết bị
- Cảnh báo khi phát hiện sự cố hoặc khi thông số vượt ngưỡng
- Giám sát kết nối VPN

## Cài đặt

### Yêu cầu

- Python 3.9+
- PostgreSQL
- Các gói phụ thuộc trong pyproject.toml

### Cấu hình môi trường

Tạo file `.env` với nội dung sau:

```
SESSION_SECRET=your_secret_key_here
FLASK_APP=run_server.py
FLASK_DEBUG=1
PYTHONPATH=.
PYTHONUNBUFFERED=1
DATABASE_URL=postgresql://postgres:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}
```

### Cài đặt dependencies

```
pip install -e .
```

## Khởi động ứng dụng

### Sử dụng Python trực tiếp

```
python run_server.py
```

hoặc

```
python run.py
```

### Sử dụng Gunicorn (cho môi trường production)

```
bash run_gunicorn.sh
```

## Đăng nhập

Tài khoản mặc định:
- Username: admin
- Password: admin

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
├── run_server.py       # Entry point chính
└── run.py              # Entry point thay thế
```