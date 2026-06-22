import os
from flask import Flask, json, render_template, request, redirect, url_for, session, send_from_directory, jsonify, flash
from flask_restful import Resource,Api,reqparse,fields,marshal_with
# from flask_sqlalchemy import SQLAlchemy
import random 
from templates.models import QuoteModel , db 

app = Flask(__name__)
#* Config 
app.config["SECRET_KEY"] = "R7^2KX@Iv@8Dr*z8"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quote.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


#! DataBase
db.init_app(app)   
 
with app.app_context():
    db.create_all()

#^ Get API 
#* get all
"""
@app.route('/api/quotes',methods=["GET"])
def get_all_quotes():
    quotes=QuoteModel.query.all()
    return jsonify([quote.to_dict() for quote in quotes])
"""
#* get random
@app.route('/api/quote/random',methods=['GET'])
def get_quote():
    quotes = QuoteModel.query.all()
    random_quote = random.choice(quotes)
    return jsonify({
            "id": random_quote.id,
            "Title":random_quote.quote_title,
            "Quote":random_quote.Quote_text,
            "Value":random_quote.value
        })

#* get by filter

@app.route('/api/quote', methods=['GET'])
def get_quotes():
    val = request.args.get('val', type=int)
    min_val = request.args.get('min_val', type=int)
    max_val = request.args.get('max_val', type=int)
    title_contains = request.args.get('title', type=str)
    quote_contains = request.args.get('quote', type=str)

    query = QuoteModel.query
    if val is not None:
        query = query.filter(QuoteModel.value == val)
    
    if min_val is not None:
        query = query.filter(QuoteModel.value >= min_val)
    
    if max_val is not None:
        query = query.filter(QuoteModel.value <= max_val)
    
    if title_contains:
        query = query.filter(QuoteModel.quote_title.ilike(f'%{title_contains}%'))
    
    if quote_contains:
        query = query.filter(QuoteModel.quote_text.ilike(f'%{quote_contains}%'))    
   
    query = query.all()

    return jsonify([
        {"id": q.id, "data":{ "Title": q.quote_title, "Quote": q.Quote_text, "Value": q.value}}
        for q in query
    ])


#^ Post 
@app.route("/api/add/",methods=["POST"])
def add_quote():
    data = request.get_json()
    quote_title = (data.get("quote_title") or "").strip()
    Quote_text = (data.get("Quote_text") or "").strip()
    if not quote_title or not Quote_text:
        return jsonify({"error": "Enter all field!"}), 400
    current_time = QuoteModel.query.count()
    add_auto_value = current_time + 1

    quoteModel = QuoteModel(
        quote_title=quote_title,
        Quote_text=Quote_text,
        value=add_auto_value
        )
    db.session.add(quoteModel)
    db.session.commit()
    
    return jsonify({"message": "Quote added",
                    "Add Quote":{
                    "ID":quoteModel.id,
                    "Title":quoteModel.quote_title,
                    "Quote":quoteModel.Quote_text,
                    "Value":quoteModel.value
                        }
                    }), 201
#^ Backend 
@app.route('/add')
def AddQuote():
    return render_template("Add.html")

@app.route('/Quote')
def SeeQuote():
    return render_template("Quotes.html")

if __name__ == '__main__':
    app.run(debug=True,port=8001)
