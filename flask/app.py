from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from templates.Database.models import db, Authentacation
import os
import uuid
from functools import wraps


UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg"}
MAX_IMG_SIZE = (300, 300)
#! -------------------------------------Configs-----------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = "R7^2KX@Iv@8Dr*z8"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Street_bazaar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)
with app.app_context():
    db.create_all()

#! -------------------------------------Avatar-----------------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_avatar(file_storage) -> str | None:
    """
    Validate, resize to thumbnail, and persist the uploaded image.
    Returns the saved filename, or None on failure.
    """
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    # Resize/crop to thumbnail with Pillow to save disk space
    img = Image.open(file_storage.stream).convert("RGB")
    img.thumbnail(MAX_IMG_SIZE, Image.LANCZOS)
    img.save(path, optimize=True, quality=85)
    return filename


def delete_old_avatar(filename: str | None):
    """Remove a previously saved avatar file from disk."""
    if not filename:
        return
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)


#! -------------------------------------Session-----------------------------------
# Single source of truth for the decorator. Used to protect pages that should
# only be visible to a logged-in user (e.g. /home). NOT applied to /login or
# /signup themselves, since that would make it impossible for a logged-out
# user to ever reach those pages (redirect loop).
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


#! ---------------------------------------RestApi-----------------------------------
#* ---------------------------------------Signup------------------------------------

@app.route("/api/signup", methods=["POST"])
def api_signup():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    shop_name = (request.form.get("shop_name") or "").strip()
    password = (request.form.get("password") or "").strip()
    confirm_password = (request.form.get("confirm_password") or "").strip()

    if not name or not email or not shop_name or not password or not confirm_password:
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 6 or len(confirm_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if password != confirm_password:
        return jsonify({"error": "Passwords must match"}), 401
    if Authentacation.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    avatar_file = request.files.get("avatar")
    avatar_name = save_avatar(avatar_file)

    hashed = generate_password_hash(password)
    authentacation = Authentacation(
        name=name,
        email=email,
        password=hashed,
        shop_name=shop_name,
        avatar=avatar_name,
    )
    db.session.add(authentacation)
    db.session.commit()

    session["user_id"] = authentacation.id
    session["user_name"] = authentacation.name
    session["user_avatar"] = authentacation.avatar_url()

    return jsonify({"message": "Account created successfully"}), 201


#* ---------------------------------------Login------------------------------------
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    authentacation = Authentacation.query.filter_by(email=email).first()
    if not authentacation or not check_password_hash(authentacation.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = authentacation.id
    session["user_name"] = authentacation.name
    session["user_avatar"] = authentacation.avatar_url()
    return jsonify({"message": "Login successful"}), 200


#* ----------------------------------------Logout-----------------------------------
@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


#!---------------------------------------Backend-----------------------------------------

@app.route('/')
def landing():
    return render_template("temps/landing.html")


@app.route('/home')
@login_required
def home():
    # Fetch the user using the ID from the session
    user = Authentacation.query.get(session["user_id"])
    return render_template("home/home.html", user=user)

@app.route('/signup')
def signup():
    # Redirect to home if already logged in
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("AuthPage/signup.html")


@app.route('/login', methods=['GET'])
def login():
    # If user is already logged in, redirect to home
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("AuthPage/login.html")


if __name__ == "__main__":
    app.run(debug=True, port=8001)