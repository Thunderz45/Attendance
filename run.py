import os
import sys
import socket

# Ensure project root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app

app = create_app()

def find_available_port(default_port=5001):
    port = int(os.environ.get('PORT', default_port))
    for p in range(port, port + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    return port

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = find_available_port(5001)
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1']

    print(f"===========================================================")
    print(f" FACE RECOGNITION BIOMETRIC ATTENDANCE SYSTEM ")
    print(f" Kiosk URL:       http://{host}:{port}/attendance")
    print(f" Admin Panel URL: http://{host}:{port}/admin")
    print(f"===========================================================")

    app.run(host=host, port=port, debug=debug)
