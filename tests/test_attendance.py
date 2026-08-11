import json
import unittest
from datetime import date, datetime
from backend.app import create_app
from backend.app.models import db, Student, FaceEmbedding, Attendance

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FACE_MATCH_THRESHOLD = 0.42

class AttendanceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            # Create Student A
            student_a = Student(
                student_id='STU-101',
                roll_number='101',
                name='Bhushan Padghan',
                course='B.Tech CS',
                year='3rd Year',
                division='Div A'
            )
            db.session.add(student_a)
            db.session.commit()
            self.student_a_id = student_a.id

            # Mock face embedding vector for Student A (512-d float list)
            mock_vector = [0.1] * 512
            embedding_a = FaceEmbedding(student_id=student_a.id)
            embedding_a.set_embedding(mock_vector)
            db.session.add(embedding_a)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_single_attendance_creation_success(self):
        with self.app.app_context():
            today = date.today()
            att = Attendance(
                student_id=self.student_a_id,
                attendance_date=today,
                attendance_time=datetime.now().time(),
                status='PRESENT',
                confidence=0.15
            )
            db.session.add(att)
            db.session.commit()

            record = Attendance.query.filter_by(student_id=self.student_a_id, attendance_date=today).first()
            self.assertIsNotNone(record)
            self.assertEqual(record.status, 'PRESENT')

    def test_mandatory_duplicate_attendance_prevention_at_database_level(self):
        """
        MANDATORY REQUIREMENT TEST:
        Verify that a student CANNOT mark attendance more than once on the same date.
        The database UNIQUE constraint (student_id, attendance_date) MUST block duplicate creation.
        """
        with self.app.app_context():
            today = date.today()

            # 1. First recognition -> Create attendance
            att1 = Attendance(
                student_id=self.student_a_id,
                attendance_date=today,
                attendance_time=datetime.now().time(),
                status='PRESENT'
            )
            db.session.add(att1)
            db.session.commit()

            # 2. Verify exactly 1 attendance record exists
            count_after_first = Attendance.query.filter_by(student_id=self.student_a_id, attendance_date=today).count()
            self.assertEqual(count_after_first, 1)

            # 3. Second recognition attempt on SAME DATE -> Expect IntegrityError at DB level
            att2 = Attendance(
                student_id=self.student_a_id,
                attendance_date=today,
                attendance_time=datetime.now().time(),
                status='PRESENT'
            )
            db.session.add(att2)

            with self.assertRaises(Exception): # IntegrityError / FlushError
                db.session.commit()

            db.session.rollback()

            # 4. Confirm still EXACTLY 1 record in database (no duplicate inserted)
            count_after_second = Attendance.query.filter_by(student_id=self.student_a_id, attendance_date=today).count()
            self.assertEqual(count_after_second, 1)

if __name__ == '__main__':
    unittest.main()
