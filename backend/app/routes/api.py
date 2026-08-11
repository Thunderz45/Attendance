from flask import Blueprint, Response, request, jsonify
from flask_login import login_required
from ..services.report_service import report_service

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/export/csv')
@login_required
def export_csv():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')
    course = request.args.get('course')
    division = request.args.get('division')

    csv_data = report_service.export_to_csv(start_date, end_date, search, course, division)
    filename = f"attendance_report_{start_date or 'all'}_to_{end_date or 'all'}.csv"

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@api_bp.route('/export/excel')
@login_required
def export_excel():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')
    course = request.args.get('course')
    division = request.args.get('division')

    excel_bytes = report_service.export_to_excel(start_date, end_date, search, course, division)
    filename = f"attendance_report_{start_date or 'all'}_to_{end_date or 'all'}.xlsx"

    return Response(
        excel_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@api_bp.route('/stats/dashboard')
@login_required
def dashboard_stats():
    target_date = request.args.get('date')
    stats = report_service.get_dashboard_stats(target_date)
    return jsonify(stats)
