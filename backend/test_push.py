import os
from app import create_app
from config import db
from models import PushSubscription
from utils import send_push_notification, PYWEBPUSH_AVAILABLE

app = create_app()

with app.app_context():
    print("--- WebPush Diagnostics ---")
    print(f"PyWebPush Installed: {PYWEBPUSH_AVAILABLE}")
    print(f"VAPID Public Key Length: {len(app.config.get('VAPID_PUBLIC_KEY', ''))}")
    print(f"VAPID Private Key Length: {len(app.config.get('VAPID_PRIVATE_KEY', ''))}")
    
    subs = PushSubscription.query.all()
    print(f"Total Subscriptions in DB: {len(subs)}")
    
    if len(subs) > 0:
        target_sub = subs[-1]
        print(f"Testing push to User ID: {target_sub.user_id}")
        print(f"Endpoint URL: {target_sub.endpoint[:50]}...")
        
        # Test direct push
        user = target_sub.user
        try:
            successes = send_push_notification(user, "Diag Test", "This is a raw diagnostic push test")
            print(f"Push Result: {successes} successful deliveries.")
        except Exception as e:
            print("CRITICAL CRASH DURING PUSH:")
            import traceback
            traceback.print_exc()
    else:
        print("No subscriptions found to test.")
