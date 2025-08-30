# firebase_setup.py

import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK
def initialize_firebase():
    cred = credentials.Certificate('path/to/your/serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    print("Firebase initialized.")

# Function to send push notification
def send_push_notification(token, title, message):
    """Send push notification to the user."""
    try:
        # Prepare message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message
            ),
            token=token
        )
        
        # Send message
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
    except Exception as e:
        print(f"Error sending message: {e}")
