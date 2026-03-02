from flask_login import login_required, current_user
from flask import jsonify
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from config import db
from models import User, Student, Attendance, Outpass, LeaveRequest, Report, Notice

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# --- Dashboard ---
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role.lower() != "admin":
        flash("You must be logged in as Admin to access the dashboard.", "danger")
        return redirect(url_for("auth_bp.login"))

    students = Student.query.all()
    attendance_records = Attendance.query.all()
    outpasses = Outpass.query.all()
    leave_requests = LeaveRequest.query.all()
    unresolved_reports = Report.query.filter_by(status="Pending").order_by(Report.date_submitted.desc()).all()
    resolved_reports = Report.query.filter(Report.status != "Pending").order_by(Report.date_submitted.desc()).all()
    notices = Notice.query.all()

    edit_id = request.args.get('edit_id', type=int)
    edit_student = None
    if edit_id:
        edit_student = Student.query.get(edit_id) 
    
    attendance_sessions = db.session.query(Attendance.marked_at).distinct().order_by(Attendance.marked_at.desc()).all()
    attendance_sessions = [s.marked_at.strftime("%Y-%m-%d %I:%M %p") for s in attendance_sessions]

    return render_template(
        "admin_dashboard.html",
        students=students,
        attendance_records=attendance_records,
        outpasses=outpasses,
        leave_requests=leave_requests,
        unresolved_reports=unresolved_reports,
        resolved_reports=resolved_reports,
        notices=notices,
        edit_student=edit_student, 
        attendance_sessions=attendance_sessions
    )

# --- Add Student ---
@admin_bp.route("/add_student", methods=["GET", "POST"])
@login_required
def add_student():
    if current_user.role.lower() != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth_bp.login"))

    if request.method == "POST":
        student = Student(
            student_id=request.form["student_id"],
            student_name=request.form["student_name"],
            room_number=request.form["room_number"],
            floor_number=request.form["floor_number"],
            student_contact=request.form["student_contact"],
            student_email=request.form.get("student_email") or None,
            address=request.form["address"],
            father_name=request.form["father_name"],
            mother_name=request.form["mother_name"],
            parent_contact=request.form["parent_contact"],
            parent_address = request.form.get("parent_address") or "", # or use request.form["parent_address"] if required

            parent_email=request.form["parent_email"],
            guardian_name=request.form["guardian_name"],
            guardian_contact=request.form["guardian_contact"],
            guardian_address=request.form["guardian_address"],
            guardian_email=request.form["guardian_email"],
            
        )
        db.session.add(student)
        db.session.commit()

        

        # Create user account for student
        user = User(
            username=student.student_id,
            email=student.student_email or student.parent_email or student.guardian_email,
            role="Student",
            student_id=student.id,
            is_first_login=True
        )
        user.set_password(student.student_id)  # temporary password = student_id
        db.session.add(user)
        db.session.commit()

        # --- Send welcome email ---
        recipient_email = student.student_email or student.parent_email or student.guardian_email
        if recipient_email:
            try:
                from flask_mail import Message
                from config import mail
                msg = Message(
                    subject="Welcome to StuTrack – Your Account Details",
                    recipients=[recipient_email]
                )
                login_url = url_for('auth_bp.login', _external=True)
                msg.body = f"""
Dear {student.student_name},

Welcome to StuTrack – the hostel management system of St Joseph's University.

Your account has been created successfully.

🔐 **Login Credentials**  
User ID: {student.student_id}  
Temporary Password: {student.student_id}  

Please log in at: {login_url}

⚠️ This is your first login. You will be required to change your password immediately after logging in.

If you have any questions, please contact the hostel administration.

Best regards,  
StuTrack Admin Team
"""
                mail.send(msg)
                flash("Welcome email sent to student.", "success")
            except Exception as e:
                flash(f"Student created but welcome email could not be sent: {str(e)}", "warning")
        else:
            flash("Student created, but no email address provided for notifications.", "info")
        # ---------------------------

        flash("Student and login created successfully!", "success")
        return redirect(url_for("admin.dashboard", _anchor="add-student"))

    return render_template("admin_add_student.html")

# --- Attendance ---
def send_absent_notification(student_email, student_name, marked_at):
    from flask_mail import Message
    from config import mail
    subject = "Absent Marked - StuTrack"
    body = f"Dear {student_name},\n\nYou have been marked ABSENT on {marked_at.strftime('%Y-%m-%d at %H:%M')}.\n\nRegards,\nAdmin"
    msg = Message(subject, recipients=[student_email], body=body)
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

@admin_bp.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    if current_user.role.lower() != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    if request.method == "POST":
        # Get date and time from form
        attendance_date = request.form.get("date")
        attendance_time = request.form.get("time")
        if not attendance_date or not attendance_time:
            return jsonify({"success": False, "message": "Date and time required."}), 400

        try:
            marked_at = datetime.strptime(f"{attendance_date} {attendance_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date/time format."}), 400

        saved_records = []
        absent_students = []  # collect (email, name) for notifications

        for key, value in request.form.items():
            if key.startswith("status_"):
                student_db_id = key.split("_")[1]
                student = Student.query.get(student_db_id)
                if student:
                    new_record = Attendance(
                        student_id=student.id,
                        room_number=student.room_number,
                        floor_number=student.floor_number,
                        marked_at=marked_at,
                        status=value
                    )
                    db.session.add(new_record)
                    saved_records.append(new_record)
                    
                    from utils import send_push_notification
                    if student.user:
                        send_push_notification(student.user, "Attendance Update", f"You have been marked {value.upper()} for {marked_at.strftime('%Y-%m-%d %H:%M')}.", url="/student/dashboard#attendance")
                        
                    if value == "Absent" and student.student_email:
                        absent_students.append((student.student_email, student.student_name))

        db.session.commit()
        saved_count = len(saved_records)

        # Send emails (simple loop; consider background task later)
        for email, name in absent_students:
            send_absent_notification(email, name, marked_at)

        # Fetch distinct recent sessions for the history list
        recent_sessions = db.session.query(Attendance.marked_at)\
                            .distinct().order_by(Attendance.marked_at.desc()).limit(20).all()
        sessions = [s.marked_at.strftime("%Y-%m-%d %I:%M %p") for s in recent_sessions]

        return jsonify({
            "success": True,
            "message": f"Attendance saved for {saved_count} students.",
            "sessions": sessions
        })

    # GET request – redirect to dashboard with anchor
    return redirect(url_for("admin.dashboard", _anchor="attendance"))

@admin_bp.route("/attendance/session/<path:datetime_str>")
@login_required
def attendance_session(datetime_str):
    if current_user.role.lower() != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        start_time = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")
        from datetime import timedelta
        end_time = start_time + timedelta(seconds=59)
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    records = Attendance.query.filter(Attendance.marked_at.between(start_time, end_time)).all()
    data = [{
        "student_id": r.student.student_id,
        "student_name": r.student.student_name,
        "status": r.status
    } for r in records]
    return jsonify({"records": data})

# --- Outpass ---
@admin_bp.route("/outpass", methods=["GET", "POST"])
@login_required
def outpass():
    if current_user.role.lower() != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth_bp.login"))

    if request.method == "POST":
        flash("Outpass processed!", "success")
        return redirect(url_for("admin.outpass"))

    outpasses = Outpass.query.all()
    return render_template("outpass.html", outpasses=outpasses)

@admin_bp.route("/leave/approve/<int:leave_id>", methods=["POST"])
@login_required
def approve_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    leave_date_str = data.get("leave_date")
    return_date_str = data.get("return_date")
    modified = False

    # Process leave date if provided
    if leave_date_str:
        try:
            new_leave = datetime.strptime(leave_date_str, "%Y-%m-%d").date()
            if new_leave != leave.leave_date:
                leave.approved_leave_date = new_leave
                modified = True
        except ValueError:
            return jsonify({"error": "Invalid leave date format. Use YYYY-MM-DD"}), 400
    else:
        leave.approved_leave_date = leave.leave_date

    # Process return date if provided
    if return_date_str:
        try:
            new_return = datetime.strptime(return_date_str, "%Y-%m-%d").date()
            if new_return != leave.return_date:
                leave.approved_return_date = new_return
                modified = True
        except ValueError:
            return jsonify({"error": "Invalid return date format. Use YYYY-MM-DD"}), 400
    else:
        leave.approved_return_date = leave.return_date

    if not modified:
        # No changes – still set approved dates to original
        leave.approved_leave_date = leave.leave_date
        leave.approved_return_date = leave.return_date
    else:
        leave.dates_modified = True

    leave.status = "Approved"
    db.session.commit()
    
    from utils import send_push_notification
    send_push_notification(leave.student.user, "Leave Request Approved", f"Your leave request for {leave.leave_date} has been approved.", url="/student/dashboard#leave")
    
    return jsonify({"message": "Leave request approved successfully"})
    return jsonify({"message": "Leave request approved successfully"})

@admin_bp.route("/leave/reject/<int:leave_id>", methods=["POST"])
@login_required
def reject_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    leave.status = "Rejected"
    db.session.commit()
    
    from utils import send_push_notification
    send_push_notification(leave.student.user, "Leave Request Rejected", f"Your leave request for {leave.leave_date} has been rejected.", url="/student/dashboard#leave")
    
    return jsonify({"message": "Leave request rejected successfully"})

# --- Notice ---
#@admin_bp.route("/notice", methods=["GET", "POST"])
#@login_required
#def notice():
   # if current_user.role.lower() != "admin":
        #flash("Access denied.", "danger")
      #  return redirect(url_for("auth_bp.login"))

#    if request.method == "POST":
       # title=request.form.get("title")
        #message = request.form.get("message")
        # You might want to add expiry_date field in the form
       # notice = Notice(
           # title=title,
           # description=message,
            #posted_on=datetime.now().date(),
            #expiry_date=None  # or from form if you add it
        #)
        #db.session.add(notice)
        #db.session.commit()
        #flash("Notice posted successfully!", "success")
        #return redirect(url_for("admin.dashboard", _anchor="notice"))
    #return render_template("admin/notice.html")


# --- Reports ---
@admin_bp.route("/reports")
@login_required
def reports():
    if current_user.role.lower() != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth_bp.login"))

    reports = Report.query.all()
    return render_template("admin/reports.html", reports=reports)

# --- Leave Requests ---
@admin_bp.route("/leave_requests", methods=["GET", "POST"])
@login_required
def leave_requests():
    if current_user.role.lower() != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth_bp.login"))

    if request.method == "POST":
        flash("Leave request processed!", "success")
        return redirect(url_for("admin.leave_requests"))

    leave_requests = LeaveRequest.query.all()
    return render_template("admin/leave_requests.html", leave_requests=leave_requests)

@admin_bp.route("/outpass/approve/<int:outpass_id>", methods=["POST"])
@login_required
def approve_outpass(outpass_id):
    outpass = Outpass.query.get_or_404(outpass_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    leave_time_str = data.get("leave_time")
    return_time_str = data.get("arrival_time")   # frontend sends key 'arrival_time' for return time

    # Keep track of whether any time was modified
    modified = False

    # Process leave time if provided
    if leave_time_str:
        try:
            new_leave = datetime.combine(
                outpass.leave_time.date(),
                datetime.strptime(leave_time_str, "%H:%M").time()
            )
            if new_leave != outpass.leave_time:
                outpass.approved_leave_time = new_leave
                modified = True
        except ValueError:
            return jsonify({"error": "Invalid leave time format. Use HH:MM"}), 400
    else:
        # If no leave time provided, keep original
        outpass.approved_leave_time = outpass.leave_time

    # Process return time if provided
    if return_time_str:
        try:
            new_return = datetime.combine(
                outpass.return_time.date(),
                datetime.strptime(return_time_str, "%H:%M").time()
            )
            if new_return != outpass.return_time:
                outpass.approved_return_time = new_return
                modified = True
        except ValueError:
            return jsonify({"error": "Invalid return time format. Use HH:MM"}), 400
    else:
        outpass.approved_return_time = outpass.return_time

    # If no modifications were made (i.e., times unchanged), still set approved times to original
    if not modified:
        outpass.approved_leave_time = outpass.leave_time
        outpass.approved_return_time = outpass.return_time
        # times_modified remains False (or unchanged)
    else:
        outpass.times_modified = True

    outpass.status = "Approved"
    db.session.commit()
    
    from utils import send_push_notification
    send_push_notification(outpass.student.user, "Outpass Approved", f"Your outpass request for {outpass.leave_time.strftime('%Y-%m-%d')} has been approved.", url="/student/dashboard#outpass")
    
    return jsonify({"message": "Outpass approved successfully"})

@admin_bp.route("/outpass/reject/<int:outpass_id>", methods=["POST"])
@login_required
def reject_outpass(outpass_id):
    if current_user.role.lower() != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    outpass = Outpass.query.get_or_404(outpass_id)
    outpass.status = "Rejected"
    db.session.commit()
    
    from utils import send_push_notification
    send_push_notification(outpass.student.user, "Outpass Rejected", f"Your outpass request has been rejected.", url="/student/dashboard#outpass")
    
    return jsonify({"message": "Outpass rejected successfully"})

@admin_bp.route("/report/resolve/<int:report_id>", methods=["POST"])
@login_required
def resolve_report(report_id):
    if current_user.role.lower() != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    report = Report.query.get_or_404(report_id)
    report.status = "Resolved"
    db.session.commit()
    
    from utils import send_push_notification
    send_push_notification(report.student.user, "Report Resolved", f"Your issue '{report.issue}' has been marked as resolved.", url="/student/dashboard#reports")
    
    return jsonify({"message": "Report marked as resolved"})

@admin_bp.route("/students")
@login_required
def student_list():
    if current_user.role.lower() != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth_bp.login"))
    
    students = Student.query.all()
    return render_template("student_list.html", students=students)

@admin_bp.route("/student/update", methods=["POST"])
@login_required
def update_student():
    if current_user.role.lower() != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth_bp.login"))

    student_id = request.form.get("student_id")  # hidden field with the database id
    student = Student.query.get_or_404(student_id)

    # Update fields (same as add student)
    student.student_id = request.form["student_id_num"]
    student.student_name = request.form["student_name"]
    student.room_number = request.form["room_number"]
    student.floor_number = request.form["floor_number"]
    student.student_contact = request.form["student_contact"]
    student.student_email = request.form.get("student_email") or None
    student.address = request.form["address"]
    student.father_name = request.form["father_name"]
    student.mother_name = request.form["mother_name"]
    student.parent_contact = request.form["parent_contact"]
    student.parent_email = request.form["parent_email"]
    student.guardian_name = request.form["guardian_name"]
    student.guardian_contact = request.form["guardian_contact"]
    student.guardian_address = request.form["guardian_address"]
    student.guardian_email = request.form["guardian_email"]

    db.session.commit()
    flash("Student updated successfully!", "success")
    return redirect(url_for("admin.dashboard", _anchor="student-list"))

from datetime import date

@admin_bp.route("/notice", methods=["GET", "POST"])
@login_required
def notice():
    if current_user.role.lower() != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth_bp.login"))

    if request.method == "POST":
        title = request.form.get("title")
        message = request.form.get("message")
        if not title or not message:
            flash("Title and message are required.", "danger")
            return redirect(url_for("admin.dashboard", _anchor="notice"))

        notice = Notice(
            title=title,
            description=message,
            posted_on=date.today(),
            expiry_date=None
        )
        db.session.add(notice)
        db.session.commit()
        
        from utils import send_push_notification
        from models import User
        
        # Notify current admin
        send_push_notification(current_user, "Notice Published", f"Notice '{title}' has been saved and shared with all students.", url="/admin/dashboard#notice")
        
        # Notify all students
        all_students = User.query.filter_by(role="Student").all()
        for student in all_students:
            send_push_notification(student, "New Notice Posted", f"Title: {title}", url="/student/dashboard#notices")
            
        flash("Notification sent successfully!", "success")
        return redirect(url_for("admin.dashboard", _anchor="notice"))
        return redirect(url_for("admin.dashboard", _anchor="notice"))

    # GET request – redirect to dashboard with send-notification panel active
    return redirect(url_for("admin.dashboard", _anchor="notice"))



