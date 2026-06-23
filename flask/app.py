
#*Modules------------------------------------------------------------------------------------------------------------------------------------------------ 
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from templates.Database.models import db, Authentacation, ProductData
import os
import uuid
from functools import wraps 

#^Image--------------------------------------------------------------------------------------------------------------------------------------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg"}
MAX_IMG_SIZE = (300, 300)

#*Config-------------------------------------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)

app.config["SECRET_KEY"] = "R7^2KX@Iv@8Dr*z8"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Street_bazaar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


#^Initialize---------------------------------------------------------------------------------------------------------------------
db.init_app(app)
with app.app_context():
    db.create_all()


#!Image-------------------------------------------------------------------------------------------------------------------------------------------------- 
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def save_avatar(file_storage) -> str | None:
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


#*Session------------------------------------------------------------------------------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


#*RestApi------------------------------------------------------------------------------------------------------------------------------------------------

#^Signup-------------------------------------------------------------------------------------------------------------------------------------------------

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


#^Login--------------------------------------------------------------------------------------------------------------------------------------------------
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

#^Logout-------------------------------------------------------------------------------------------------------------------------------------------------
@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

#^Add Product--------------------------------------------------------------------------------------------------------------------
@app.route("/api/product/add",methods=["POST"])
def api_add_product():
    data = request.get_json(silent=True)
    
    product_name           =(data.get("product_name") or "").strip()
    product_quantity       =(data.get("product_quantity") or "").strip()
    product_payment_type   =(data.get("product_payment_type") or "").strip()

    if not product_name or not product_quantity or not product_payment_type:
        return jsonify({"error":"All fields are required"}), 400
    try:
        product_quantity = int(product_quantity)
    except ValueError:
        return jsonify({"error":"Quantity must be in number"}),400
    if product_quantity<=0 or product_quantity is None:
        product_quantity=1
    add_product = ProductData(
        product_name = product_name,
        product_quantity = product_quantity,
        product_payment_type = product_payment_type
    )
    db.session.add(add_product)
    db.session.commit()    
    
    return jsonify({"Add":{"id":add_product.product_id,
                           "data":{
                                "Product Name": add_product.product_name,   
                                "Product Quantity": add_product.product_quantity,   
                                "Product PaymentType": add_product.product_payment_type,   
                    }}}),201
    
#^Get all Product-----------------------------------------------------------------------------------------------------------------
@app.route("/api/products", methods=["GET"])
def get_all_products():

    product = ProductData.query.all()

    return jsonify([
        {
            "id": products.product_id,
            "product_name": products.product_name,
            "product_quantity": products.product_quantity,
            "product_payment_type": products.product_payment_type
        }
        for products  in product
        
    ])
        
    # if not ProductData_delet



#^Delete Product-----------------------------------------------------------------------------------------------------------------
# @app.route("/api/product/delete/<int:product_id>",methods=["DELETE"])
# def adi_delete_product(product_id):
#     ProductData_delete = ProductData.query.get(product_id)
#     if not ProductData_delete:
#         return jsonify({"Error":"Data not found"}),404
#     db.session.delete(ProductData_delete)
#     db.session.commit()
#     return jsonify({"Delete":"Data Deleted successfull"}),204

# @app.route("/api/products/<int:product_id>", methods=["DELETE"])
# def delete_product(product_id):

#     product = ProductData.query.get(product_id)

#     if not product:
#         return jsonify({"error": "Product not found"}), 404

#     db.session.delete(product)
#     db.session.commit()

#     return jsonify({
#         "message": "Product deleted successfully"
#     }), 200
#*Backend------------------------------------------------------------------------------------------------------------------------------------------------

#^Signup-------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/signup')
def signup():
    # Redirect to home if already logged in
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("AuthPage/signup.html")

#^Login--------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/login', methods=['GET'])
def login():
    # If user is already logged in, redirect to home
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("AuthPage/login.html")

#^Logout-------------------------------------------------------------------------------------------------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("login")

#^Landing------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/')
def landing():
    return render_template("temps/landing.html")

#^Home---------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/home')
@login_required
def home():
    # Fetch the user using the ID from the session
    user = Authentacation.query.get(session["user_id"])
    return render_template("home/home.html", user=user)




if __name__ == "__main__":
    app.run(debug=True, port=8001)
    
