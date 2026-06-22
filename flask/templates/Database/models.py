from flask_sqlalchemy import SQLAlchemy
from flask import url_for

db = SQLAlchemy()

class Authentacation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    shop_name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    avatar = db.Column(db.String(256), nullable=True)   # filename only
    
    def avatar_url(self):
        if self.avatar:
            return url_for(
                "static",
                filename=f"uploads/{self.avatar}",
                _external=True
                )
        return self.avatar

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "shop_name": self.shop_name,
            "avatar": self.avatar_url()
        }
