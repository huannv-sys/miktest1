import os
import logging
from mik.app import create_app

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Tạo ứng dụng Flask
app = create_app()

if __name__ == '__main__':
    # Chạy ứng dụng - sử dụng 0.0.0.0 thay vì localhost để có thể truy cập từ mạng
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)