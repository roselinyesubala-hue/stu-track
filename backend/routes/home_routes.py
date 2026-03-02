from flask import Blueprint, render_template

# Create a blueprint for home routes
home_bp = Blueprint("home_bp", __name__)

@home_bp.route("/")
def home():
    # Render the home.html template
    return render_template("home.html")