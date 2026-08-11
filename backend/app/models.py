import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    roll_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    division = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    face_embedding = db.relationship('FaceEmbedding', backref='student', uselist=False, cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='student', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def has_face_registered(self):
        return self.face_embedding is not None

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'roll_number': self.roll_number,
            'name': self.name,
            'course': self.course,
            'year': self.year,
            'division': self.division,
            'email': self.email,
            'phone': self.phone,
            'active': self.active,
            'has_face': self.has_face_registered,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<Student {self.roll_number} - {self.name}>'


class FaceEmbedding(db.Model):
    __tablename__ = 'face_embeddings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, unique=True)
    embedding_data = db.Column(db.Text, nullable=False)  # JSON serialized list of floats
    sample_count = db.Column(db.Integer, default=1)
    quality_score = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_embedding(self, embedding_vector):
        if hasattr(embedding_vector, 'tolist'):
            embedding_vector = embedding_vector.tolist()
        self.embedding_data = json.dumps(embedding_vector)

    def get_embedding(self):
        if not self.embedding_data:
            return []
        return json.loads(self.embedding_data)

    def __repr__(self):
        return f'<FaceEmbedding StudentID:{self.student_id}>'


class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False, index=True)
    attendance_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='PRESENT', nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'attendance_date', name='unique_student_daily_attendance'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student.student_id,
            'roll_number': self.student.roll_number,
            'student_name': self.student.name,
            'course': self.student.course,
            'division': self.student.division,
            'attendance_date': self.attendance_date.strftime('%Y-%m-%d'),
            'attendance_time': self.attendance_time.strftime('%I:%M:%S %p'),
            'status': self.status,
            'confidence': round(self.confidence, 4) if self.confidence else None
        }

    def __repr__(self):
        return f'<Attendance StudentID:{self.student_id} Date:{self.attendance_date} Status:{self.status}>'
