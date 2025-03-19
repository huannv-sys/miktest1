from mik.app import create_app, db
from mik.app.models import User

def create_admin():
    # Tạo ứng dụng Flask
    app = create_app()
    
    with app.app_context():
        # Tạo tất cả các bảng
        db.create_all()
        
        # Kiểm tra xem đã có admin chưa
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Tạo tài khoản admin
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')  # Mật khẩu mặc định
            
            # Thêm vào database
            db.session.add(admin)
            db.session.commit()
            print("Created admin user: admin/admin123")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    create_admin()