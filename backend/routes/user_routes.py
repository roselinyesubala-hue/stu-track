# user_routes.py (completely replace with this)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from models import User
from models import db

# Note: This blueprint might be redundant with auth_bp
# Consider if you really need both
user_bp = Blueprint("user", __name__)

@user_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("user.login"))