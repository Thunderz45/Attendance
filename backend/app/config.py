import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-2026')
    db_env = os.environ.get('DATABASE_URL')
    if db_env and db_env.startswith('sqlite:///'):
        rel_path = db_env.replace('sqlite:///', '')
        if not os.path.isabs(rel_path):
            abs_db_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{abs_db_path}'
        else:
            SQLALCHEMY_DATABASE_URI = db_env
    else:
        abs_db_path = os.path.abspath(os.path.join(BASE_DIR, 'instance', 'attendance.db'))
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{abs_db_path}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Face Recognition Config
    FACE_MATCH_THRESHOLD = float(os.environ.get('FACE_MATCH_THRESHOLD', '0.42'))
    RECOGNITION_INTERVAL = int(os.environ.get('RECOGNITION_INTERVAL', '700'))
    CAMERA_WIDTH = int(os.environ.get('CAMERA_WIDTH', '640'))
    CAMERA_HEIGHT = int(os.environ.get('CAMERA_HEIGHT', '480'))

    # Firebase Config
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'attendance-a6f14')
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', 'AIzaSyA9XnOEmhr9TCjXul44_82_CdoUEN7PRKo')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', 'attendance-a6f14.firebaseapp.com')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'attendance-a6f14.firebasestorage.app')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '446821265991')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID', '1:446821265991:web:fc9299c36a6b109e04b762')
    FIREBASE_MEASUREMENT_ID = os.environ.get('FIREBASE_MEASUREMENT_ID', 'G-2FZRY9SVV7')

    FIREBASE_CONFIG = {
        'apiKey': FIREBASE_API_KEY,
        'authDomain': FIREBASE_AUTH_DOMAIN,
        'projectId': FIREBASE_PROJECT_ID,
        'storageBucket': FIREBASE_STORAGE_BUCKET,
        'messagingSenderId': FIREBASE_MESSAGING_SENDER_ID,
        'appId': FIREBASE_APP_ID,
        'measurementId': FIREBASE_MEASUREMENT_ID
    }
