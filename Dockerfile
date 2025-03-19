FROM python:3.11-slim

# Đặt biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Ho_Chi_Minh

# Tạo thư mục làm việc
WORKDIR /app

# Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Sao chép tệp yêu cầu và cài đặt các phụ thuộc Python
COPY dependencies.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r dependencies.txt

# Sao chép mã nguồn ứng dụng
COPY . .

# Tạo người dùng không đặc quyền để chạy ứng dụng
RUN useradd -m mikmon && \
    chown -R mikmon:mikmon /app

# Chuyển sang người dùng không đặc quyền
USER mikmon

# Script khởi động để đợi PostgreSQL và khởi động ứng dụng
COPY --chown=mikmon:mikmon ./docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Hiển thị cổng
EXPOSE 5050

# Mặc định sử dụng gunicorn để chạy ứng dụng
ENTRYPOINT ["/app/docker-entrypoint.sh"]