from flask_sqlalchemy import SQLAlchemy
from flask import url_for

db = SQLAlchemy()


class Authentacation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    shop_name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    avatar = db.Column(db.String(256), nullable=True)  # filename only

    def avatar_url(self):
        if self.avatar:
            return url_for("static", filename=f"uploads/{self.avatar}", _external=True)
        return self.avatar

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "shop_name": self.shop_name,
            "avatar": self.avatar_url(),
        }


class ProductData(db.Model):
    Product_id = db.Column(db.Integer, primary_key=True)
    Product_name = db.Column(db.String(220), nullable=False)
    Product_quantity = db.Column(db.Integer, nullable=False, default=1)
    Product_payment_type = db.Column(db.String(40), nullable=False)

    def to_dict(self):
        return {
            "id": self.product_id,
            "Product Name": self.product_name,
            "Product Quantity": self.product_quantity,
            "Product PaymentType": self.product_payment_type,
        }


class ClientData(db.Model):
    Client_id = db.Column(db.Integer, primary_key=True)
    Client_name = db.Column(db.String(220), nullable=False)
    Client_phone = db.Column(db.Integer, nullable=False, default=1)
    Client_product = db.Column(db.String(40), nullable=False)
    Products = ProductData
