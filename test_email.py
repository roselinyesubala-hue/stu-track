import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app
from flask_mail import Mail, Message

app = create_app()
with app.app_context():
    mail = Mail(app)
    msg = Message(
        subject="Test Email from StuTrack",
        recipients=["roselinyesubala@gmail.com"],   # replace with a real email
        body="If you receive this, email works!"
    )
    mail.send(msg)
    print("Email sent successfully!")