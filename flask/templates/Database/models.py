from flask_sqlalchemy import SQLAlchemy
from flask import url_for

db = SQLAlchemy()


class Authentacation(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    shop_name   = db.Column(db.String(250), nullable=False)
    password    = db.Column(db.String(255), nullable=False)
    avatar      = db.Column(db.String(256), nullable=True)

    @property
    def avatar_url(self):
        if self.avatar:
            return url_for("static", filename=f"uploads/{self.avatar}")
        return None

    def to_dict(self):
        return {
            "id":        self.id,
            "name":      self.name,
            "email":     self.email,
            "shop_name": self.shop_name,
            "avatar_url": self.avatar_url,
        }


class ProductData(db.Model):
    __tablename__ = "Product_data"

    ProductId      = db.Column(db.Integer, primary_key=True)
    ProductName    = db.Column(db.String(220), nullable=False)
    ProductCompany = db.Column(db.String(200), nullable=True)
    ProductPrice   = db.Column(db.Integer, nullable=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("authentacation.id"), nullable=False)

    # FIX 12 — backref name corrected; was "ProductSale" (misleading), now "product_sales"
    product_sales  = db.relationship("ProductSaleData", backref="product")

    def to_dict(self):
        return {
            "id":      self.ProductId,
            "name":    self.ProductName,
            "company": self.ProductCompany,
            "price":   self.ProductPrice,
        }


class ClientData(db.Model):
    __tablename__ = "Client_data"

    ClientId   = db.Column(db.Integer, primary_key=True)
    ClientName = db.Column(db.String(120), nullable=False)
    ClientNo   = db.Column(db.Integer)
    user_id    = db.Column(db.Integer, db.ForeignKey("authentacation.id"), nullable=False)


class ProductSaleData(db.Model):
    # FIX 1 — was `__table__ = "Product_Sale"` (wrong attr, causes the metaclass crash).
    __tablename__ = "Product_Sale"

    ProductSaleId      = db.Column(db.Integer, primary_key=True)
    ProductQuantity    = db.Column(db.Integer, nullable=False, default=1)
    ProductPaymentType = db.Column(db.String(50), nullable=False)
    IsPaymentPending   = db.Column(db.String(10))

    # FIX 12 — FK string must match ProductData.__tablename__ exactly (capital P).
    product_id = db.Column(db.Integer, db.ForeignKey("Product_data.ProductId"))
    user_id    = db.Column(db.Integer, db.ForeignKey("authentacation.id"), nullable=False)

    def to_dict(self):
        return {
            "id":                   self.ProductSaleId,
            "product_quantity":     self.ProductQuantity,
            "product_payment_type": self.ProductPaymentType,
            "is_payment_pending":   self.IsPaymentPending,
            "product_id":           self.product_id,
        }


# models.py — Defines four SQLAlchemy models for Street Bazaar.
# Authentacation stores shop-owner credentials and avatar path.
# ProductData stores the product catalogue, scoped to a user via user_id FK.
# ProductSaleData records each sale transaction and links back to ProductData;
#   the crash was caused by `__table__` (expects a Table object) instead of
#   `__tablename__` (expects a string) — one missing character, full server death.
# ClientData stores client contact info, also scoped to a user.