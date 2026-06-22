from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class QuoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_title = db.Column(db.String(200), nullable=False)
    Quote_text = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            "id": self.id,
            "quote_title": self.quote_title,
            "Quote": self.Quote_text,
            "Value": self.value
        }
