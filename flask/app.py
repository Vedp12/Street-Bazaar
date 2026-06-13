from flask import Flask, render_template, request, redirect, url_for
import os
app = Flask(__name__)


IMG_FOLDER = os.path.join("static", "IMG")

app.config["UPLOAD_FOLDER"] = IMG_FOLDER

@app.route('/')
def landing():
    return render_template("landing.html")


@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/signup_man')
def signup_man():
    return render_template("signup_man.html")


@app.route('/signup_shop')
def signup_shop():
    return render_template("signup_shop.html")

@app.route("/home")
def home(): 
    return render_template("home.html")

@app.route('/inventory')
def inventory():
    return render_template("inventory.html")

@app.route('/inventory_add_product')
def inventory_add_product():
    return render_template("inventory_add_product.html")

@app.route('/profile_name')
def profile_name():
    return render_template("profile_name.html")

@app.route('/profile_shop')
def profile_shop():
    return render_template('profile_shop.html')

@app.route('/profile_dashboard')
def profile_dashboard():
    return render_template("profile_dashboard.html")

if __name__ == "__main__":
    app.run(debug=True,port="8001")
    