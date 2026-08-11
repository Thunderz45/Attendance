from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
# pyrefly: ignore [missing-import]
from flask_login import login_required
from ..models import db, Student, FaceEmbedding, Attendance
from ..services.report_service import report_service
from ..services.face_service import face_service
from ..services.firebase_service import firebase_service

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    stats = report_service.get_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/students')
@login_required
def students():
    search = request.args.get('search', '').strip()
    course = request.args.get('course', '').strip()
    division = request.args.get('division', '').strip()

    query = Student.query.filter_by(active=True)

    if search:
        term = f"%{search}%"
        query = query.filter(
            (Student.name.ilike(term)) |
            (Student.roll_number.ilike(term)) |
            (Student.student_id.ilike(term))
        )
    if course:
        query = query.filter_by(course=course)
    if division:
        query = query.filter_by(division=division)

    students_list = query.order_by(Student.roll_number).all()

    # Get distinct courses & divisions for filter dropdowns
    courses = db.session.query(Student.course).filter_by(active=True).distinct().all()
    divisions = db.session.query(Student.division).filter_by(active=True).distinct().all()

    return render_template(
        'admin/students.html',
        students=students_list,
        courses=[c[0] for c in courses],
        divisions=[d[0] for d in divisions],
        search=search,
        selected_course=course,
        selected_division=division
    )

@admin_bp.route('/students/register', methods=['GET', 'POST'])
@login_required
def register_student():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        name = request.form.get('name', '').strip()
        course = request.form.get('course', '').strip()
        year = request.form.get('year', '').strip()
        division = request.form.get('division', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        # Validation
        if not all([student_id, roll_number, name, course, year, division]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/register_student.html')

        # Check unique student_id / roll_number
        if Student.query.filter_by(student_id=student_id).first():
            flash(f'Student ID "{student_id}" is already registered.', 'danger')
            return render_template('admin/register_student.html')

        if Student.query.filter_by(roll_number=roll_number).first():
            flash(f'Roll Number "{roll_number}" is already registered.', 'danger')
            return render_template('admin/register_student.html')

        student = Student(
            student_id=student_id,
            roll_number=roll_number,
            name=name,
            course=course,
            year=year,
            division=division,
            email=email or None,
            phone=phone or None,
            active=True
        )

        db.session.add(student)
        db.session.commit()
        firebase_service.sync_student(student.to_dict())

        flash(f'Student {name} registered successfully! Now register face biometrics.', 'success')
        return redirect(url_for('admin.register_face', student_id=student.id))

    return render_template('admin/register_student.html')

@admin_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = db.get_or_404(Student, student_id)

    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        student.course = request.form.get('course', '').strip()
        student.year = request.form.get('year', '').strip()
        student.division = request.form.get('division', '').strip()
        student.email = request.form.get('email', '').strip() or None
        student.phone = request.form.get('phone', '').strip() or None

        db.session.commit()
        flash(f'Updated details for {student.name}.', 'success')
        return redirect(url_for('admin.students'))

    return render_template('admin/edit_student.html', student=student)

@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    # Soft delete (deactivate)
    student.active = False
    db.session.commit()
    flash(f'Student {student.name} ({student.roll_number}) has been deactivated.', 'info')
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/<int:student_id>/register-face', methods=['GET', 'POST'])
@login_required
def register_face(student_id):
    student = db.get_or_404(Student, student_id)
    return render_template('admin/register_face.html', student=student)

@admin_bp.route('/students/<int:student_id>/save-face', methods=['POST'])
@login_required
def save_face(student_id):
    student = db.get_or_404(Student, student_id)

    data = request.get_json() or {}
    images = data.get('images', [])

    if not images or len(images) < 1:
        return jsonify({'success': False, 'message': 'No face frames received.'}), 400

    embeddings = []

    for idx, base64_img in enumerate(images):
        img = face_service.decode_base64_image(base64_img)
        if img is None:
            continue

        faces = face_service.detect_faces(img)
        if len(faces) == 0:
            return jsonify({'success': False, 'message': f'Frame #{idx+1}: No face detected. Position face inside frame.'}), 400
        elif len(faces) > 1:
            return jsonify({'success': False, 'message': f'Frame #{idx+1}: Multiple faces detected. Only one person allowed.'}), 400

        vector = face_service.extract_face_embedding(img, faces[0])
        if vector is not None:
            embeddings.append(vector)

    if not embeddings:
        return jsonify({'success': False, 'message': 'Could not extract valid face embedding. Please try again with clear lighting.'}), 400

    # Calculate average embedding vector
    avg_embedding = [float(val) for val in (sum(map(lambda v: v[i], embeddings)) / len(embeddings) for i in range(len(embeddings[0])))]

    # Check if this face already belongs to another registered active student
    other_embeddings = db.session.query(Student, FaceEmbedding.embedding_data)\
        .join(FaceEmbedding, Student.id == FaceEmbedding.student_id)\
        .filter(Student.active == True, Student.id != student_id).all()

    registered_tuples = []
    for s, emb_str in other_embeddings:
        import json
        registered_tuples.append((s, json.loads(emb_str)))

    existing_match, dist = face_service.find_matching_student(avg_embedding, registered_tuples, threshold=0.38)
    if existing_match:
        return jsonify({
            'success': False,
            'message': f'Face matches an existing student: {existing_match.name} (Roll No: {existing_match.roll_number}). Duplicate biometric registration is prohibited.'
        }), 400

    # Save or update FaceEmbedding record
    face_record = FaceEmbedding.query.filter_by(student_id=student.id).first()
    if not face_record:
        face_record = FaceEmbedding(student_id=student.id)
        db.session.add(face_record)

    face_record.set_embedding(avg_embedding)
    face_record.sample_count = len(embeddings)
    face_record.quality_score = 1.0
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Face biometrics registered successfully for {student.name}!',
        'redirect_url': url_for('admin.students')
    })

@admin_bp.route('/students/<int:student_id>/remove-face', methods=['POST'])
@login_required
def remove_face(student_id):
    student = db.get_or_404(Student, student_id)
    if student.face_embedding:
        db.session.delete(student.face_embedding)
        db.session.commit()
        flash(f'Removed biometric face data for {student.name}.', 'info')
    return redirect(url_for('admin.students'))

@admin_bp.route('/records')
@login_required
def records():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    search = request.args.get('search', '').strip()
    course = request.args.get('course', '').strip()
    division = request.args.get('division', '').strip()

    attendance_list = report_service.get_attendance_records(
        start_date=start_date or None,
        end_date=end_date or None,
        search_query=search or None,
        course=course or None,
        division=division or None
    )

    courses = db.session.query(Student.course).filter_by(active=True).distinct().all()
    divisions = db.session.query(Student.division).filter_by(active=True).distinct().all()

    return render_template(
        'admin/records.html',
        records=attendance_list,
        courses=[c[0] for c in courses],
        divisions=[d[0] for d in divisions],
        start_date=start_date,
        end_date=end_date,
        search=search,
        selected_course=course,
        selected_division=division
    )

@admin_bp.route('/reports')
@login_required
def reports():
    date_preset = request.args.get('preset', 'today')
    custom_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))

    try:
        target_date = datetime.strptime(custom_date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()

    if date_preset == 'yesterday':
        target_date = date.today() - timedelta(days=1)
    elif date_preset == 'today':
        target_date = date.today()

    stats = report_service.get_dashboard_stats(target_date=target_date)
    present_records = report_service.get_attendance_records(start_date=target_date, end_date=target_date)
    absent_students = report_service.get_absent_students(target_date=target_date)

    return render_template(
        'admin/reports.html',
        stats=stats,
        present_records=present_records,
        absent_students=absent_students,
        date_preset=date_preset,
        selected_date=target_date.strftime('%Y-%m-%d')
    )

@admin_bp.route('/privacy')
def privacy():
    return render_template('admin/privacy.html')
