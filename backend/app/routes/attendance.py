import json
import logging
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from ..models import db, Student, FaceEmbedding, Attendance
from ..services.face_service import face_service
from ..services.firebase_service import firebase_service

attendance_bp = Blueprint('attendance', __name__)
logger = logging.getLogger(__name__)

@attendance_bp.route('/attendance')
def kiosk():
    return render_template('attendance/kiosk.html')

@attendance_bp.route('/api/attendance/recognize', methods=['POST'])
def recognize():
    data = request.get_json() or {}
    image_b64 = data.get('image')

    if not image_b64:
        return jsonify({'status': 'ERROR', 'message': 'No image frame provided.'}), 400

    img = face_service.decode_base64_image(image_b64)
    if img is None:
        return jsonify({'status': 'ERROR', 'message': 'Invalid image encoding.'}), 400

    # 1. Detect faces
    faces = face_service.detect_faces(img)
    if len(faces) == 0:
        return jsonify({'status': 'NO_FACE', 'message': 'Looking for face...'})
    elif len(faces) > 1:
        return jsonify({
            'status': 'MULTIPLE_FACES',
            'message': 'Multiple faces detected. Only one person should be visible.'
        })

    # 2. Extract candidate embedding vector
    candidate_vector = face_service.extract_face_embedding(img, faces[0])
    if candidate_vector is None:
        return jsonify({'status': 'NO_FACE', 'message': 'Face position unclear or image blurry.'})

    # 3. Load active registered student face embeddings
    active_embeddings = db.session.query(Student, FaceEmbedding.embedding_data)\
        .join(FaceEmbedding, Student.id == FaceEmbedding.student_id)\
        .filter(Student.active == True).all()

    if not active_embeddings:
        return jsonify({
            'status': 'UNRECOGNIZED',
            'message': 'No registered student face database found. Contact Admin.'
        })

    registered_tuples = []
    for student_obj, emb_json_str in active_embeddings:
        try:
            vec = json.loads(emb_json_str)
            registered_tuples.append((student_obj, vec))
        except Exception:
            continue

    # 4. Perform distance matching against threshold
    match_threshold = current_app.config.get('FACE_MATCH_THRESHOLD', 0.42)
    matched_student, match_distance = face_service.find_matching_student(
        candidate_vector,
        registered_tuples,
        threshold=match_threshold
    )

    if not matched_student:
        return jsonify({
            'status': 'UNRECOGNIZED',
            'message': 'Face Not Recognized'
        })

    # 5. Check attendance logic & enforce DB duplicate rule
    today_date = date.today()
    now_dt = datetime.now()
    now_time = now_dt.time()

    # Query existing attendance for today
    existing_attendance = Attendance.query.filter_by(
        student_id=matched_student.id,
        attendance_date=today_date
    ).first()

    student_data = {
        'student_id': matched_student.student_id,
        'roll_number': matched_student.roll_number,
        'name': matched_student.name,
        'course': matched_student.course,
        'division': matched_student.division
    }

    if existing_attendance:
        return jsonify({
            'status': 'ALREADY_MARKED',
            'message': 'Attendance Already Marked',
            'student': student_data,
            'attendance_time': existing_attendance.attendance_time.strftime('%I:%M:%S %p'),
            'attendance_date': existing_attendance.attendance_date.strftime('%d-%b-%Y')
        })

    # Try creating new attendance record
    try:
        new_attendance = Attendance(
            student_id=matched_student.id,
            attendance_date=today_date,
            attendance_time=now_time,
            status='PRESENT',
            confidence=float(match_distance)
        )
        db.session.add(new_attendance)
        db.session.commit()
        firebase_service.sync_attendance(new_attendance.to_dict())

        return jsonify({
            'status': 'SUCCESS',
            'message': 'Attendance Marked Successfully',
            'student': student_data,
            'attendance_time': now_time.strftime('%I:%M:%S %p'),
            'attendance_date': today_date.strftime('%d-%b-%Y')
        })
    except IntegrityError:
        # DB UNIQUE constraint (student_id, attendance_date) caught race condition or duplicate
        db.session.rollback()
        existing_attendance = Attendance.query.filter_by(
            student_id=matched_student.id,
            attendance_date=today_date
        ).first()

        return jsonify({
            'status': 'ALREADY_MARKED',
            'message': 'Attendance Already Marked',
            'student': student_data,
            'attendance_time': existing_attendance.attendance_time.strftime('%I:%M:%S %p') if existing_attendance else now_time.strftime('%I:%M:%S %p'),
            'attendance_date': today_date.strftime('%d-%b-%Y')
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking attendance: {str(e)}")
        return jsonify({
            'status': 'ERROR',
            'message': 'Database error while saving attendance record.'
        }), 500
