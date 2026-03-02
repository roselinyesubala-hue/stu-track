from backend.app import db
from backend.models.user import User
from werkzeug.security import generate_password_hash

def seed_admin():
    # Check if admin already exists
    existing_admin = User.query.filter_by(username="admin").first()
    if not existing_admin:
        admin_user = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            is_first_login=False
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    seed_admin()