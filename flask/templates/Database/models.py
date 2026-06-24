from flask_sqlalchemy import SQLAlchemy
from flask import url_for

db = SQLAlchemy()


class Authentacation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    shop_name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(256), nullable=True)

    products = db.relationship("ProductData", backref="owner", lazy=True)

    # FIX 5: Must be a @property so the template can access it as {{ user.avatar_url }}
    # without the decorator it renders as "<bound method ...>" instead of the URL string.
    @property
    def avatar_url(self):
        if self.avatar:
            return url_for("static", filename=f"uploads/{self.avatar}")
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "shop_name": self.shop_name,
            "avatar_url": self.avatar_url,
        }


class ProductData(db.Model):
    Product_id = db.Column(db.Integer, primary_key=True)
    Product_name = db.Column(db.String(220), nullable=False)
    Product_quantity = db.Column(db.Integer, nullable=False, default=1)
    Product_payment_type = db.Column(db.String(40), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("authentacation.id"), nullable=False)

    # Template accesses product.id, product.product_name, etc. (snake_case).
    # These properties bridge the PascalCase DB columns to what the template expects,
    # so neither the template nor the column names need to change.
    @property
    def id(self):
        return self.Product_id

    @property
    def product_name(self):
        return self.Product_name

    @property
    def product_quantity(self):
        return self.Product_quantity

    @property
    def product_payment_type(self):
        return self.Product_payment_type

    def to_dict(self):
        return {
            "id": self.Product_id,
            "product_name": self.Product_name,
            "product_quantity": self.Product_quantity,
            "product_payment_type": self.Product_payment_type,
        }