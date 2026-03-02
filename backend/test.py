from app import create_app
from models import User
from config import db
from datetime import datetime, timedelta
import secrets

try:
    app = create_app()
    with app.app_context():
        users = User.query.filter(User.reset_token != None).all()
        with open('tokens.txt', 'w') as f:
            for u in users:
                is_valid = datetime.utcnow() <= u.reset_token_expiry
                f.write(f"Username: {u.username}, Token: {u.reset_token}, Expiry: {u.reset_token_expiry}, Now: {datetime.utcnow()}, Valid: {is_valid}\n")
except Exception as e:
    with open('error.txt', 'w') as f:
        f.write(str(e))
