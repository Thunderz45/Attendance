import unittest
from backend.app import create_app
from backend.app.models import db, Admin, Student

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FACE_MATCH_THRESHOLD = 0.42

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            # Create test admin
            admin = Admin(username='testadmin', email='test@admin.com')
            admin.set_password('Secret123')
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_login_success(self):
        response = self.client.post('/admin/login', data={
            'username': 'testadmin',
            'password': 'Secret123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard Overview', response.data)

    def test_admin_login_failure(self):
        response = self.client.post('/admin/login', data={
            'username': 'testadmin',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_protected_route_requires_login(self):
        response = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.location)

if __name__ == '__main__':
    unittest.main()
