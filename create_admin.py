from simple_flask_server import app, db, User
from datetime import datetime

def create_admin():
    """Create an administrator user if none exists"""
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Administrator user already exists")
            return
        
        # Create new admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            created_at=datetime.utcnow()
        )
        admin.set_password('admin123')  # Default password, should be changed immediately
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        print("Administrator user created successfully")

if __name__ == '__main__':
    create_admin()