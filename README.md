# MikroTik Monitor

Hệ thống giám sát và quản lý thiết bị MikroTik với hiệu suất cao và bảo mật tốt.

## Tính năng

- Giám sát thiết bị MikroTik theo thời gian thực
- Cảnh báo khi phát hiện vấn đề
- Sao lưu và phục hồi cấu hình
- Theo dõi hiệu suất mạng
- Bản đồ mạng trực quan
- Giao diện người dùng hiện đại và thân thiện

## Yêu cầu

- Python 3.8+
- Pip
- Các thư viện phụ thuộc (xem file `pyproject.toml`)

## Cài đặt

1. Clone repository này:
   ```
   git clone https://github.com/yourusername/mikrotik-monitor.git
   cd mikrotik-monitor
   ```

2. Tạo và kích hoạt môi trường ảo:
   ```
   python -m venv venv
   source venv/bin/activate  # Trên Windows: venv\Scripts\activate
   ```

3. Cài đặt các gói phụ thuộc:
   ```
   pip install -r requirements.txt
   ```

4. Tạo file cấu hình:
   ```
   cp .env.sample .env
   ```

5. Chỉnh sửa file `.env` với các cài đặt phù hợp cho môi trường của bạn.

## Chạy ứng dụng

1. Khởi động ứng dụng:
   ```
   python main.py
   ```

2. Truy cập ứng dụng qua trình duyệt tại địa chỉ:
   ```
   http://localhost:5000
   ```

3. Đăng nhập với tài khoản mặc định:
   - Username: admin
   - Password: admin123

## Cấu hình

Các tùy chọn cấu hình chính:

- `SECRET_KEY`: Khóa bí mật cho ứng dụng Flask
- `JWT_SECRET_KEY`: Khóa bí mật cho JWT
- `DATABASE_URL`: URL kết nối đến cơ sở dữ liệu
- `MIKROTIK_CONNECTION_TIMEOUT`: Thời gian chờ kết nối với thiết bị MikroTik (giây)

Xem thêm các tùy chọn trong file `.env.sample`.

## Bảo mật

Trong môi trường sản xuất, hãy đảm bảo:

- Thay đổi mật khẩu admin mặc định
- Sử dụng khóa bí mật mạnh và ngẫu nhiên
- Bật SSL/TLS cho kết nối HTTPS
- Cấu hình đúng các quyền truy cập cơ sở dữ liệu

## Phát triển

1. Fork repository này
2. Tạo branch tính năng mới (`git checkout -b feature/amazing-feature`)
3. Commit các thay đổi (`git commit -m 'Add some amazing feature'`)
4. Push lên branch (`git push origin feature/amazing-feature`)
5. Tạo Pull Request mới

## Giấy phép

Phân phối theo Giấy phép MIT. Xem `LICENSE` để biết thêm thông tin.

## Liên hệ

Tên của bạn - email@example.com

Link dự án: [https://github.com/yourusername/mikrotik-monitor](https://github.com/yourusername/mikrotik-monitor)