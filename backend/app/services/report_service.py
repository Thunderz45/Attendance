import io
from datetime import datetime, date, timedelta
import pandas as pd
from ..models import db, Student, Attendance, FaceEmbedding

class ReportService:
    @staticmethod
    def get_dashboard_stats(target_date=None):
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        total_students = Student.query.filter_by(active=True).count()
        total_registered_faces = db.session.query(FaceEmbedding)\
            .join(Student, FaceEmbedding.student_id == Student.id)\
            .filter(Student.active == True).count()

        present_today = Attendance.query.filter_by(attendance_date=target_date)\
            .join(Student, Attendance.student_id == Student.id)\
            .filter(Student.active == True).count()

        absent_today = max(0, total_students - present_today)
        attendance_percentage = round((present_today / total_students * 100), 1) if total_students > 0 else 0.0

        recent_attendances = Attendance.query.filter_by(attendance_date=target_date)\
            .join(Student, Attendance.student_id == Student.id)\
            .filter(Student.active == True)\
            .order_by(Attendance.attendance_time.desc())\
            .limit(10).all()

        return {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'total_students': total_students,
            'registered_faces': total_registered_faces,
            'present_today': present_today,
            'absent_today': absent_today,
            'attendance_percentage': attendance_percentage,
            'recent_attendances': [a.to_dict() for a in recent_attendances]
        }

    @staticmethod
    def get_attendance_records(start_date=None, end_date=None, search_query=None, course=None, division=None):
        query = Attendance.query.join(Student, Attendance.student_id == Student.id).filter(Student.active == True)

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.attendance_date <= end_date)

        if search_query:
            term = f"%{search_query}%"
            query = query.filter(
                (Student.name.ilike(term)) |
                (Student.roll_number.ilike(term)) |
                (Student.student_id.ilike(term))
            )

        if course:
            query = query.filter(Student.course == course)

        if division:
            query = query.filter(Student.division == division)

        records = query.order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).all()
        return [r.to_dict() for r in records]

    @staticmethod
    def get_absent_students(target_date):
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        # Get all present student IDs for date
        present_student_ids = db.session.query(Attendance.student_id)\
            .filter(Attendance.attendance_date == target_date).all()
        present_ids = [p[0] for p in present_student_ids]

        # Active students not in present_ids
        absent_students = Student.query.filter(
            Student.active == True,
            ~Student.id.in_(present_ids) if present_ids else True
        ).order_by(Student.roll_number).all()

        return [s.to_dict() for s in absent_students]

    @staticmethod
    def export_attendance_dataframe(start_date=None, end_date=None, search_query=None, course=None, division=None):
        records = ReportService.get_attendance_records(start_date, end_date, search_query, course, division)
        if not records:
            df = pd.DataFrame(columns=['Sr. No.', 'Date', 'Time', 'Student ID', 'Roll Number', 'Student Name', 'Course', 'Division', 'Status'])
            return df

        data = []
        for idx, r in enumerate(records, 1):
            data.append({
                'Sr. No.': idx,
                'Date': r['attendance_date'],
                'Time': r['attendance_time'],
                'Student ID': r['student_id'],
                'Roll Number': r['roll_number'],
                'Student Name': r['student_name'],
                'Course': r['course'],
                'Division': r['division'],
                'Status': r['status']
            })

        return pd.DataFrame(data)

    @staticmethod
    def export_to_csv(start_date=None, end_date=None, search_query=None, course=None, division=None):
        df = ReportService.export_attendance_dataframe(start_date, end_date, search_query, course, division)
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def export_to_excel(start_date=None, end_date=None, search_query=None, course=None, division=None):
        df = ReportService.export_attendance_dataframe(start_date, end_date, search_query, course, division)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance Report')
        output.seek(0)
        return output.getvalue()

report_service = ReportService()
