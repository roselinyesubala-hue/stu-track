import os
import json
from pywebpush import webpush, WebPushException

# The same keys generated in config.py
VAPID_PRIVATE_KEY = "dummy_for_testing" # I will extract from config
VAPID_PUBLIC_KEY = "dummy_for_testing"

# I will query the DB for the raw strings to avoid Flask app context blocking

import sqlite3
import mysql.connector

try:
    print("Connecting to DB to fetch subscriptions directly...")
    import pymysql
    connection = pymysql.connect(host='localhost', user='root', password='Rose@1979', database='stu_track')
    with connection.cursor() as cursor:
        cursor.execute("SELECT endpoint, p256dh, auth FROM push_subscription ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            print("Found subscription:")
            print(f"Endpoint: {result[0][:50]}...")
            print("To actually test this, we need the live keys from config.py.")
        else:
            print("No subscriptions found in the database. The frontend never successfully subscribed.")
except Exception as e:
    print(f"DB Error: {e}")
