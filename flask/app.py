from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
    Blueprint,
    send_from_directory,
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

from templates.Database.models import db, Authentacation, ProductData
from functools import wraps
import os
import uuid


UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg"}
MAX_IMG_SIZE = (300, 300)


app = Flask(__name__)
app.config["SECRET_KEY"] = "R7^2KX@Iv@8Dr*z8"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Street_bazaar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


db.init_app(app)


with app.app_context():
    db.create_all()


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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))

        user = Authentacation.query.get(session["user_id"])
        if not user:
            session.clear()
            flash("Your account seems to be missing. Please log in again.", "error")
            return redirect(url_for("login"))

        return f(user, *args, **kwargs)

    return decorated_function


@app.route("/api/signup", methods=["POST"])
def api_signup():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    shop_name = request.form.get("shop_name", "").strip()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    avatar_file = request.files.get("avatar")

    if not all([name, email, shop_name, password, confirm_password]):
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if Authentacation.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 409

    avatar_filename = save_avatar(avatar_file)
    if avatar_file and not avatar_filename:
        return (
            jsonify(
                {"error": "Invalid file type for avatar. Allowed: png, jpg, jpeg."}
            ),
            400,
        )

    hashed_password = generate_password_hash(password)

    new_user = Authentacation(
        name=name,
        email=email,
        shop_name=shop_name,
        password=hashed_password,
        avatar=avatar_filename,
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        session["user_name"] = new_user.name

        return (
            jsonify(
                {
                    "message": "Account created and logged in successfully",
                    "user_id": new_user.id,
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error during signup: {e}")

        if avatar_filename:
            delete_old_avatar(avatar_filename)
        return (
            jsonify(
                {"error": "An internal error occurred during signup. Please try again."}
            ),
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

    if user and check_password_hash(user.password, password):
        session["user_id"] = user.id
        session["user_name"] = user.name

        return jsonify({"message": "Login successful", "user_id": user.id}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    user_id_to_clear = session.get("user_id")
    session.clear()
    app.logger.info(f"User {user_id_to_clear} logged out.")
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/api/product/add", methods=["POST"])
@login_required
def api_add_product(current_user):
    data = request.get_json(silent=True) or {}

    product_name = data.get("Product_name", "").strip()
    product_quantity_raw = data.get("Product_quantity")
    product_payment_type = data.get("Product_payment_type", "").strip()

    if not product_name or product_quantity_raw is None or not product_payment_type:
        return (
            jsonify({"error": "Product name, quantity, and payment type are required"}),
            400,
        )

    try:
        product_quantity = int(product_quantity_raw)
        if product_quantity <= 0:
            product_quantity = 1
    except (ValueError, TypeError):
        return jsonify({"error": "Product quantity must be a valid number"}), 400

    new_product = ProductData(
        Product_name=product_name,
        Product_quantity=product_quantity,
        Product_payment_type=product_payment_type,
        user_id=current_user.id,
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Product added successfully",
                    "product": new_product.to_dict(),
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding product for user {current_user.id}: {e}")
        return (
            jsonify({"error": "An internal error occurred while adding the product."}),
            500,
        )


@app.route("/api/products", methods=["GET"])
@login_required
def get_all_products(current_user):

    products = ProductData.query.filter_by(user_id=current_user.id).all()

    product_list = [p.to_dict() for p in products]

    return jsonify(product_list), 200


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(current_user, product_id: int):

    product = ProductData.query.filter_by(
        Product_id=product_id, user_id=current_user.id
    ).first()

    if not product:
        return (
            jsonify(
                {
                    "error": "Product not found or you do not have permission to delete it."
                }
            ),
            404,
        )

    try:
        db.session.delete(product)
        db.session.commit()
        return (
            jsonify({"message": f"Product with ID {product_id} deleted successfully."}),
            200,
        )
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Error deleting product {product_id} for user {current_user.id}: {e}"
        )
        return (
            jsonify(
                {"error": "An internal error occurred while deleting the product."}
            ),
            500,
        )


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

    user_id_to_clear = session.get("user_id")
    session.clear()
    app.logger.info(f"User {user_id_to_clear} logged out via page redirect.")

    return redirect(url_for("login"))


@app.route("/")
def landing():

    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("temps/landing.html")


@app.route("/home")
@login_required
def home(current_user):

    products = ProductData.query.filter_by(user_id=current_user.id).all()

    return render_template("home/home.html", user=current_user, Products=products)


if __name__ == "__main__":

    app.run(debug=True, port=8001)
