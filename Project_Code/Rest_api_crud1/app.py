"""
Street Bazaar - Shop Auth
Features: signup/login, profile image upload, edit profile, hashed passwords
"""

import os
import uuid
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

# ── Config ───────────────────────────────────────────────────────────────────
UPLOAD_FOLDER   = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXT     = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_IMG_SIZE    = (400, 400)   # resize to square thumbnail

app = Flask(__name__)
app.config["SECRET_KEY"]              = "change-this-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shop.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"]           = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"]      = 5 * 1024 * 1024   # 5 MB cap

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ── Model ─────────────────────────────────────────────────────────────────────
class User(db.Model):
    """Shop owner — password is always stored as a hash, never plaintext."""
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    avatar     = db.Column(db.String(256), nullable=True)   # filename only

    def avatar_url(self):
        """Return a usable URL for the avatar, or None."""
        if self.avatar:
            return url_for("static", filename=f"uploads/{self.avatar}")
        return None

    def to_dict(self):
        return {
            "id":        self.id,
            "name":      self.name,
            "email":     self.email,
            "avatar_url": self.avatar_url(),
        }

# ── Helpers ───────────────────────────────────────────────────────────────────
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

    ext      = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path     = os.path.join(app.config["UPLOAD_FOLDER"], filename)

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

def login_required(fn):
    """Decorator: redirect to login if session has no user."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return fn(*args, **kwargs)
    return wrapper

# ── REST API — Auth ───────────────────────────────────────────────────────────
@app.route("/api/signup", methods=["POST"])
def api_signup():
    """
    POST /api/signup  (multipart/form-data)
    Fields: name, email, password, avatar (optional file)
    """
    name     = (request.form.get("name")     or "").strip()
    email    = (request.form.get("email")    or "").strip().lower()
    password = (request.form.get("password") or "").strip()

    # Guard clauses
    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    avatar_file = request.files.get("avatar")
    avatar_name = save_avatar(avatar_file)   # None if not provided

    hashed = generate_password_hash(password)
    user   = User(name=name, email=email, password=hashed, avatar=avatar_name)
    db.session.add(user)
    db.session.commit()

    # Persist minimal info in session
    session["user_id"]    = user.id
    session["user_name"]  = user.name
    session["user_avatar"] = user.avatar_url()
    return jsonify({"message": "Account created", "user": user.to_dict()}), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    """
    POST /api/login  (JSON)
    Body: { email, password }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"]     = user.id
    session["user_name"]   = user.name
    session["user_avatar"] = user.avatar_url()
    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


# ── REST API — Profile edit ───────────────────────────────────────────────────
@app.route("/api/profile", methods=["PUT"])
@login_required
def api_update_profile():
    """
    PUT /api/profile  (multipart/form-data)
    Fields: name, email, current_password (required),
            new_password (optional), avatar (optional file)
    Updates allowed fields; ignores blank/missing ones.
    """
    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Verify current password before any change
    current_pw = (request.form.get("current_password") or "").strip()
    if not current_pw:
        return jsonify({"error": "Current password is required to save changes"}), 400
    if not check_password_hash(user.password, current_pw):
        return jsonify({"error": "Current password is incorrect"}), 403

    # ── Name ──
    new_name = (request.form.get("name") or "").strip()
    if new_name:
        user.name = new_name

    # ── Email ──
    new_email = (request.form.get("email") or "").strip().lower()
    if new_email and new_email != user.email:
        conflict = User.query.filter_by(email=new_email).first()
        if conflict:
            return jsonify({"error": "Email already in use by another account"}), 409
        user.email = new_email

    # ── New password ──
    new_pw = (request.form.get("new_password") or "").strip()
    if new_pw:
        if len(new_pw) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400
        user.password = generate_password_hash(new_pw)

    # ── Avatar ──
    avatar_file = request.files.get("avatar")
    if avatar_file and avatar_file.filename:
        if not allowed_file(avatar_file.filename):
            return jsonify({"error": "Invalid image format. Use PNG, JPG, WEBP, or GIF"}), 400
        delete_old_avatar(user.avatar)      # remove previous file from disk
        user.avatar = save_avatar(avatar_file)

    db.session.commit()

    # Refresh session values
    session["user_name"]   = user.name
    session["user_avatar"] = user.avatar_url()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200


# ── Page routes ───────────────────────────────────────────────────────────────
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("home.html", user=user)

@app.route("/signup")
def signup():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("signup.html")

@app.route("/login")
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/edit")
def edit_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("edit.html", user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
