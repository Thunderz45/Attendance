import unittest
from backend.app import create_app
from backend.app.models import db, Admin, Student, FaceEmbedding

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FACE_MATCH_THRESHOLD = 0.42

class StudentTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            admin = Admin(username='admin')
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()

        # Login
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'Admin@123'})

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_student_registration(self):
        response = self.client.post('/admin/students/register', data={
            'student_id': 'STU-101',
            'roll_number': '101',
            'name': 'Bhushan Padghan',
            'course': 'Computer Science',
            'year': '3rd Year',
            'division': 'Div A',
            'email': 'bhushan@college.edu'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            student = Student.query.filter_by(roll_number='101').first()
            self.assertIsNotNone(student)
            self.assertEqual(student.name, 'Bhushan Padghan')

    def test_duplicate_student_roll_rejection(self):
        with self.app.app_context():
            s1 = Student(student_id='STU-101', roll_number='101', name='Student A', course='CS', year='1st Year', division='A')
            db.session.add(s1)
            db.session.commit()

        response = self.client.post('/admin/students/register', data={
            'student_id': 'STU-102',
            'roll_number': '101', # Duplicate roll number
            'name': 'Student B',
            'course': 'CS',
            'year': '1st Year',
            'division': 'A'
        }, follow_redirects=True)

        self.assertTrue(
            b'Roll Number &#34;101&#34; is already registered' in response.data or
            b'Roll Number &quot;101&quot; is already registered' in response.data or
            b'already registered' in response.data
        )

if __name__ == '__main__':
    unittest.main()
