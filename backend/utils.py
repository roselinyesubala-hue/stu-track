# backend/utils.py - Utility functions for StuTrack

import json
try:
    from pywebpush import webpush, WebPushException
    PYWEBPUSH_AVAILABLE = True
except ImportError:
    PYWEBPUSH_AVAILABLE = False
    print("Warning: pywebpush not found. Push notifications will be disabled.")
from flask import current_app
from models import PushSubscription

def send_push_notification(user, title, message, url='/'):
    """Send a browser push notification to a specific user."""
    if not PYWEBPUSH_AVAILABLE:
        print(f"Skipping push notification for user {user.id} (pywebpush missing)")
        return 0

    subscriptions = PushSubscription.query.filter_by(user_id=user.id).all()
    
    if not subscriptions:
        print(f"No push subscriptions found for user {user.id}")
        return

    payload = json.dumps({
        "title": title,
        "body": message,
        "url": url
    })

    vapid_private_key = current_app.config.get("VAPID_PRIVATE_KEY")
    vapid_public_key = current_app.config.get("VAPID_PUBLIC_KEY")
    vapid_claims = {"sub": current_app.config.get("VAPID_CLAIM_EMAIL")}

    success_count = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                },
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            success_count += 1
        except WebPushException as ex:
            print(f"WebPush error for user {user.id}: {ex}")
            # If the endpoint is no longer valid, we should probably remove it
            if ex.response is not None and ex.response.status_code in [404, 410]:
                from config import db
                db.session.delete(sub)
                db.session.commit()
        except Exception as e:
            print(f"General error sending push to user {user.id}: {e}")

    return success_count
