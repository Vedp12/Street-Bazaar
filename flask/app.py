from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from functools import wraps
import os
import uuid

from templates.Database.models import (
    db,
    Authentacation,
    ProductData,
    ProductSaleData,
    ClientData,
)


UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg"}
MAX_IMG_SIZE = (300, 300)


app = Flask(__name__)
app.config["SECRET_KEY"] = "R7^2KX@Iv@8Dr*z8"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Street_bazaar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # Flip to True when on HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()


# ── Helpers ──────────────────────────────────────────────────────────────────


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_avatar(file_storage) -> str | None:
    if not file_storage or file_storage.filename == "":
        return None
    filename_original = secure_filename(file_storage.filename)
    if not allowed_file(filename_original):
        return None
    try:
        ext = filename_original.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        img = Image.open(file_storage.stream).convert("RGB")
        img.thumbnail(MAX_IMG_SIZE, Image.Resampling.LANCZOS)
        img.save(path, optimize=True, quality=85)
        return unique_filename
    except Exception as e:
        app.logger.error(f"Error saving avatar: {e}")
        return None


def delete_old_avatar(filename: str | None):
    if not filename:
        return
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError as e:
            app.logger.error(f"Error deleting avatar {filename}: {e}")


# ── Auth decorator ────────────────────────────────────────────────────────────


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))

        user = db.session.get(Authentacation, session["user_id"])
        if not user:
            session.clear()
            flash("Your account seems to be missing. Please log in again.", "error")
            return redirect(url_for("login"))

        return f(user, *args, **kwargs)

    return decorated_function


# ── API routes ────────────────────────────────────────────────────────────────


@app.route("/api/signup", methods=["POST"])
def api_signup():
    # FIX 1 — removed stray request.get_json(); this endpoint receives multipart/form-data,
    # not JSON. Calling get_json() here is a no-op at best and misleading at worst.

    # FIX 2 — was request.form.get("name") but the frontend sends the key "Username".
    # Mismatched key → empty string → "All fields are required" error every time.
    Username = request.form.get("Username", "").strip()
    shopName = request.form.get("shopName", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()
    confirmPassword = request.form.get("confirmPassword", "").strip()

    # FIX 3 — was request.files.get("avatarFile") but the frontend appends the file
    # under the key "avatar". Wrong key → file_storage is always None → avatar never saved.
    avatar_file = request.files.get("avatar")

    if not Username or not email or not shopName or not password or not confirmPassword:
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if password != confirmPassword:
        return jsonify({"error": "Passwords do not match"}), 400
    if Authentacation.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 409

    avatar_filename = save_avatar(avatar_file)
    if avatar_file and avatar_file.filename and not avatar_filename:
        return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg."}), 400

    new_user = Authentacation(
        name=Username,
        email=email,
        shopName=shopName,
        password=generate_password_hash(password),
        avatar=avatar_filename,
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        session["user_name"] = new_user.name
        return (
            jsonify(
                {"message": "Account created successfully", "user_id": new_user.id}
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Signup error: {e}")
        delete_old_avatar(avatar_filename)
        return (
            jsonify({"error": "Internal error during signup. Please try again."}),
            500,
        )


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = Authentacation.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user.id
    session["user_name"] = user.name
    return jsonify({"message": "Login successful", "user_id": user.id}), 200


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout(current_user):
    uid = session.get("user_id")
    session.clear()
    app.logger.info(f"User {uid} logged out.")
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/api/product/add", methods=["POST"])
@login_required
def api_add_product(current_user):
    data = request.get_json(silent=True) or {}
    ProductName = data.get("ProductName", "").strip()
    ProductCompany = data.get("ProductCompany", "").strip()
    ProductPrice = data.get("ProductPrice")

    if not ProductName:
        return jsonify({"error": "Product name is required"}), 400

    # FIX 7 — was instantiating ProductSaleData (a sale/transaction record) instead of
    # ProductData (a catalogue entry). api_add_product adds to the product catalogue.
    new_product = ProductData(
        ProductName=ProductName,
        ProductCompany=ProductCompany or None,
        ProductPrice=int(ProductPrice) if ProductPrice is not None else None,
        user_id=current_user.id,
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        return (
            jsonify({"message": "Product added", "product": new_product.to_dict()}),
            201,
        )
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Add product error for user {current_user.id}: {e}")
        return jsonify({"error": "Internal error while adding product."}), 500


@app.route("/api/products", methods=["GET"])
@login_required
def get_all_products(current_user):
    products = ProductData.query.filter_by(user_id=current_user.id).all()
    return jsonify({"products": [p.to_dict() for p in products]}), 200


@app.route("/signup")
def signup():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("AuthPage/signup.html")


@app.route("/login", methods=["GET"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("AuthPage/login.html")


@app.route("/logout")
def logout():
    uid = session.get("user_id")
    session.clear()
    app.logger.info(f"User {uid} logged out via redirect.")
    return redirect(url_for("login"))


@app.route("/")
def landing():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("temps/landing.html")


@app.route("/home")
@login_required
def home(current_user):
    products = ProductSaleData.query.filter_by(user_id=current_user.id).all()
    productsale_list = [p.to_dict() for p in products]
    return render_template(
        "home/home.html", user=current_user, product=productsale_list
    )


if __name__ == "__main__":
    app.run(debug=True, port=8001)
