# firebase_setup.py
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize the Firebase Admin SDK
cred = credentials.Certificate('path/to/your/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
