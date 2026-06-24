from flask_sqlalchemy import SQLAlchemy
from flask import url_for
import os # Import os for checking file existence

db = SQLAlchemy()

class Authentacation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    shop_name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    avatar = db.Column(db.String(256), nullable=True)  # filename only

    # Relationship to ProductData (one-to-many)
    products = db.relationship('ProductData', backref='owner', lazy=True)

    def avatar_url(self):
        if self.avatar:
            # Ensure the file actually exists before generating URL
            # This is a good practice, though not strictly required by Flask itself
            # if os.path.exists(os.path.join('your_project', 'static', 'uploads', self.avatar)): # Adjust path if needed
            return url_for('static', filename=f'uploads/{self.avatar}')
        return None # Return None if no avatar

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "shop_name": self.shop_name,
            "avatar_url": self.avatar_url(), # Use a clearer key for frontend
        }

class ProductData(db.Model):
    Product_id = db.Column(db.Integer, primary_key=True)
    Product_name = db.Column(db.String(220), nullable=False)
    Product_quantity = db.Column(db.Integer, nullable=False, default=1)
    Product_payment_type = db.Column(db.String(40), nullable=False)

    # Foreign Key to link products to users
    user_id = db.Column(db.Integer, db.ForeignKey('authentacation.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.Product_id, # Consistent ID key
            "product_name": self.Product_name, # Use snake_case for consistency
            "product_quantity": self.Product_quantity,
            "product_payment_type": self.Product_payment_type,
        }