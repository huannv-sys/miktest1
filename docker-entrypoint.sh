#!/bin/bash
set -e

# Chờ PostgreSQL khởi động
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL..."
    
    # Trích xuất thông tin kết nối từ DATABASE_URL
    # Định dạng URL: postgresql://user:password@host:port/dbname
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:/]+):?([0-9]*)/([^?]+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASSWORD="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]:-5432}"
        DB_NAME="${BASH_REMATCH[5]}"
        
        # Đợi cho đến khi PostgreSQL khả dụng
        until nc -z "$DB_HOST" "$DB_PORT"; do
            echo "PostgreSQL is unavailable - sleeping"
            sleep 1
        done
        
        echo "PostgreSQL is up - continuing"
    else
        echo "Warning: Unable to parse DATABASE_URL, skipping PostgreSQL check"
    fi
fi

# Tạo admin user nếu cần
python create_admin.py

# Nếu có đối số, thì chạy với đối số đó
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    # Mặc định chạy với gunicorn
    exec gunicorn --workers 2 --bind 0.0.0.0:5000 app:app
fi