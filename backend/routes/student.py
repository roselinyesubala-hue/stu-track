# student.py (updated)
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import Student, Attendance, Outpass, LeaveRequest, Report, Notice
from config import db

# Use a consistent blueprint name
student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
def dashboard():
    """Load student dashboard with all data"""
    # Ensure user is a student
    if current_user.role != "Student":
        flash("Access denied. Student privileges required.", "danger")
        return redirect(url_for("auth_bp.login"))
    
    # Get student record
    student = Student.query.get(current_user.student_id)
    if not student:
        flash("Student profile not found.", "danger")
        return redirect(url_for("auth_bp.logout"))
    
    # Get all related data
   # In student.py, inside dashboard() function
    attendance = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.marked_at.desc()).all()
    outpasses = Outpass.query.filter_by(student_id=student.id).all()
    leave_requests = LeaveRequest.query.filter_by(student_id=student.id).all()
    reports = Report.query.filter_by(student_id=student.id).all()
    from sqlalchemy import or_
    notices = Notice.query.filter(or_(Notice.expiry_date >= datetime.now().date(), Notice.expiry_date.is_(None))).all()


    return render_template(
        "student_dashboard.html",
        student=student,
        attendance=attendance,
        outpasses=outpasses,
        leave_requests=leave_requests,
        reports=reports,
        notices=notices,
    
    )

@student_bp.route("/profile")
@login_required
def profile():
    """View profile (redirects to dashboard with profile panel)"""
    return redirect(url_for("student.dashboard", _anchor="profile"))

@student_bp.route("/attendance")
@login_required
def attendance():
    """View attendance (redirects to dashboard with attendance panel)"""
    return redirect(url_for("student.dashboard", _anchor="attendance"))

@student_bp.route("/outpass", methods=["POST"])
@login_required
def outpass():
    """Submit a new outpass request"""
    student = Student.query.get(current_user.student_id)
    
    try:
        outpass = Outpass(
            student_id=student.id,
            room_number=request.form["room_number"],
            floor_number=request.form["floor_number"],
            place=request.form["place"],
            reason=request.form.get("reason", ""),
            leave_time=datetime.fromisoformat(request.form["leave_time"]),
            return_time=datetime.fromisoformat(request.form["return_time"]),
            status="Pending"
        )
        db.session.add(outpass)
        db.session.commit()
        from utils import send_push_notification
        from models import User
        
        # Notify student
        send_push_notification(current_user, "Outpass Submitted", "Your outpass request has been submitted successfully.", url="/student/dashboard#outpass")
        
        # Notify admins
        admins = User.query.filter_by(role="Admin").all()
        for admin in admins:
            send_push_notification(admin, "New Outpass Request", f"{student.student_name} submitted a new outpass request.", url="/admin/dashboard#outpass")
            
        flash("Outpass request submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting outpass: {str(e)}", "danger")
    
    return redirect(url_for("student.dashboard", _anchor="outpass"))

@student_bp.route("/leave", methods=["POST"])
@login_required
def leave():
    """Submit a new leave request"""
    student = Student.query.get(current_user.student_id)
    
    try:
        leave_request = LeaveRequest(
            student_id=student.id,
            room_number=request.form["room_number"],
            floor_number=request.form["floor_number"],
            reason=request.form["reason"],
            leave_date=datetime.fromisoformat(request.form["leave_date"]).date(),
            return_date=datetime.fromisoformat(request.form["return_date"]).date(),
            status="Pending"
        )
        db.session.add(leave_request)
        db.session.commit()
        from utils import send_push_notification
        from models import User
        
        # Notify student
        send_push_notification(current_user, "Leave Request Submitted", "Your leave request has been submitted successfully.", url="/student/dashboard#leave")
        
        # Notify admins
        admins = User.query.filter_by(role="Admin").all()
        for admin in admins:
            send_push_notification(admin, "New Leave Request", f"{student.student_name} submitted a new leave request.", url="/admin/dashboard#leave")
            
        flash("Leave request submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting leave request: {str(e)}", "danger")
    
    return redirect(url_for("student.dashboard", _anchor="leave"))

@student_bp.route("/reports", methods=["POST"])
@login_required
def reports():
    """Submit a new report"""
    student = Student.query.get(current_user.student_id)
    
    try:
        report = Report(
            student_id=student.id,
            room_number=request.form["room_number"],
            floor_number=request.form["floor_number"],
            issue=request.form["issue"],
            description=request.form.get("description"),
            date_submitted=datetime.now(),
            status="Pending"
        )
        db.session.add(report)
        db.session.commit()
        from utils import send_push_notification
        from models import User
        
        # Notify student
        send_push_notification(current_user, "Report Submitted", f"Your report on '{report.issue}' has been submitted.", url="/student/dashboard#reports")
        
        # Notify admins
        admins = User.query.filter_by(role="Admin").all()
        for admin in admins:
            send_push_notification(admin, "New Report Submitted", f"{student.student_name} submitted a new issue: {report.issue}", url="/admin/dashboard#reports")
            
        flash("Report submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting report: {str(e)}", "danger")
    
    return redirect(url_for("student.dashboard", _anchor="reports"))

# API endpoints for dynamic loading
@student_bp.route("/api/attendance")
@login_required
def api_attendance():
    """JSON endpoint for attendance data"""
    if current_user.role != "Student":
        return jsonify({"error": "Unauthorized"}), 403
    
    student = Student.query.get(current_user.student_id)
    records = Attendance.query.filter_by(student_id=student.id).all()
    
    return jsonify([{
        "date": r.marked_at.strftime('%Y-%m-%d'),
        "time": r.marked_at.strftime('%I:%M %p'),
        "status": r.status
    } for r in records])

@student_bp.route("/api/notices")
@login_required
def api_notices():
    """JSON endpoint for notices"""

    from sqlalchemy import or_

    notices = Notice.query.filter( or_(Notice.expiry_date >= datetime.now().date(), Notice.expiry_date.is_(None))).all()
    return jsonify([{
        "title": n.title,
        "description": n.description,
        "posted_on": n.posted_on.isoformat()
    } for n in notices])