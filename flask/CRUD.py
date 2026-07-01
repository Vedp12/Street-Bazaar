# ? CRUD api
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# * Initialise DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///book.db"
db = SQLAlchemy(app)


#! DB model
class shelfs(db.Model):
    __tablename__ = "shelves"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    book = db.relationship(
        "books", lazy=True, backref="shelfs", cascade="all, delete-orphan"
    )


class books(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer)
    pages = db.Column(db.Integer)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelves.id"), nullable=False)


with app.app_context():
    db.create_all()


#! Backend
# *Shelf----------------------------------------------------------------------------------------


# TODO Post -> add Shelf
@app.route("/shelf", methods=["POST"])
def create_shelf():
    data = request.get_json()
    shelf = shelfs(name=data["name"])
    db.session.add(shelf)
    db.session.commit()
    return jsonify({"Sucess": f"shelf saved to DB at id {shelf.id}"}), 201


# TODO Get -> shelf by id
@app.route("/shelf/<int:id>", methods=["GET"])
def get_shelf(id):
    Shelf = shelfs.query.get(id)
    if Shelf:
        return jsonify(
            {
                "ID": Shelf.id,
                "name": Shelf.name,
                "Book": [
                    {
                        "Id": books.id,
                        "title": books.title,
                        "price": books.price,
                        "pages": books.pages,
                    }
                    for books in Shelf.book
                ],
            }
        )
    else:
        return {"error": "Shelf's ID not found"}, 404


# TODO Get -> all Shelf
@app.route("/shelf", methods=["GET"])
def get_Allshelf():
    Shelfs = shelfs.query.all()
    # total = sum(Shelfs.book)
    allShelf = []
    if Shelfs:
        for Shelf in Shelfs:
            allShelf.append(
                {
                    "book": [
                        {
                            "id": Book.id,
                            "title": Book.title,
                            "price": Book.price,
                            "pages": Book.pages,
                        }
                        for Book in (Shelf.book)
                    ],
                    "id": Shelf.id,
                    "name": Shelf.name,
                    "total": len(Shelf.book),
                }
            )
        return jsonify(allShelf), 200
    else:
        return {"error": "ID not found"}, 404


# *Book----------------------------------------------------------------------------------------


# TODO Post -> add book
@app.route("/shelf/book", methods=["POST"])
def create_book():
    data = request.get_json()
    shelf = shelfs.query.get(data["shelf_id"])
    if shelf is None:
        return jsonify({"error": "Shelf ID did not find "}), 404
    book = books(
        title=data["title"],
        price=data["price"],
        pages=data["pages"],
        shelf_id=data["shelf_id"],
    )
    db.session.add(book)
    db.session.commit()
    return jsonify({"Sucess": f"shelf saved at DB "})


# TODO Patch -> change each attribute of book by id
@app.route("/shelf/book/<int:id>", methods=["PATCH"])
def PATCH_book(id):

    Book = books.query.get(id)
    if Book is None:
        return jsonify({"error": "Book ID did not find "}), 404
    data = request.get_json()
    if "title" in data:
        Book.title = data["title"]
    if "pages" in data:
        Book.pages = data["pages"]
    if "price" in data:
        Book.price = data["price"]
    db.session.commit()
    return jsonify({"Update": f"Data at ID {Book.id} updated"})


# TODO Put -> Change all attribute by id
@app.route("/shelf/book/<int:id>", methods=["PUT"])
def PUT_book(id):
    Book = books.query.get(id)
    data = request.get_json()
    if Book:
        Book.title = data.get("title", Book.title)
        Book.price = data.get("price", Book.price)
        Book.pages = data.get("pages", Book.pages)
        db.session.commit()
        return jsonify({"Update": f"Data at ID {Book.id} updated"})
    else:
        return jsonify({"error": "Book ID did not find "}), 404


# TODO Delete -> Delete data by id
@app.route("/shelf/book/<int:id>", methods=["DELETE"])
def DELETE_book(id):
    Book = books.query.get(id)
    if Book:
        db.session.delete(Book)
        db.session.commit()
        return jsonify({"Message": "Id deleted successfully!"})
    else:
        return jsonify({"Error": "Id does not exist"})


# TODO Get ->  book by filter
@app.route("/shelf/book", methods=["GET"])
def get_book():
    MINprice = request.args.get("MINprice", type=int)
    MAXprice = request.args.get("MAXprice", type=int)
    title_contains = request.args.get("title_contains", type=str)
    query = books.query
    if MINprice is not None:
        query = query.filter(books.price >= MINprice)
    if MAXprice is not None:
        query = query.filter(books.price <= MAXprice)
    if title_contains is not None:
        query = query.filter(books.title.ilike(f"%{title_contains}%"))

    booklist = query.all()
    return jsonify(
        {
            "Book": [
                {
                    "Id": book.id,
                    "title": book.title,
                    "price": book.price,
                    "pages": book.pages,
                }
                for book in booklist
            ],
        }
    )


# TODO Get -> book by id
@app.route("/shelf/book/<int:id>", methods=["GET"])
def get_Allbook(id):
    Book = books.query.get(id)
    if Book:
        return jsonify(
            {
                "id": Book.id,
                "title": Book.title,
                "price": Book.price,
                "pages": Book.pages,
            }
        )
    else:
        return jsonify({"Error": "Book's Id not found"}), 404


app.run(debug=True)
