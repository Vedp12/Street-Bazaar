# ? CRUD With API
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from faker import Faker

app = Flask(__name__)

# * Initialise DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///book.db"
db = SQLAlchemy(app)
fake = Faker()


#! DB model
class shelfs(db.Model):
    __tablename__ = "shelves"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    book = db.relationship(
        "books", lazy=True, backref="shelfs", cascade="all, delete-orphan"
    )


class author(db.Model):
    __tablename__ = "Authors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    book = db.relationship(
        "books", lazy=True, backref="author", cascade="all, delete-orphan"
    )


class books(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer)
    pages = db.Column(db.Integer)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelves.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("Authors.id"))
    person = db.relationship(
        "Persons", lazy=True, backref="books", cascade="all, delete-orphan"
    )


class person(db.Model):
    __tablename__ = "Persons"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    profession = db.Column(db.String)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))


with app.app_context():
    db.create_all()


#! Backend
# *Shelf----------------------------------------------------------------------------------------

# TODO Post -> add Shelf


@app.route("/shelf", methods=["POST"])
def create_shelf():
    data = request.get_json()
    # Use the Faker instance to generate a name
    shelf = shelfs(name=fake.name())  # Assuming your model is named Shelf, not shelfs
    db.session.add(shelf)
    db.session.commit()
    return jsonify({"Success": f"Shelf saved to DB at id {shelf.id}"}), 201


# TODO GET -> shelf by id
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


# *Author----------------------------------------------------------------------------------------
# TODO POST -> add author
@app.route("/author", methods=["POST"])
def create_author():
    data = request.get_json()
    Author = author(name=data["name"])
    db.session.add(Author)
    db.session.commit()
    return jsonify({"message", f"Author named {Author.name} added at ID {Author.id}"})


# TODO Patch -> Patch each data by id
@app.route("/author/<int:id>")
def patch_author():
    Author = author.query.get(id)
    data = request.get_json()
    prev_name = Author.name
    Author.name = data["name"]
    db.session.commit()
    return jsonify(
        {"UPDATE": f"Author name updated from {prev_name}  to {Author.name}"}
    )


# TODO Delete -> Delete author by id
@app.route("/delete", methods=["DELETE"])
def delete_author():
    Author = author.query.get(id)
    if Author:
        db.session.delete(Author)
        return jsonify({"DELETE": "Author data updated"})
    else:
        return jsonify({"Error": f"{Author} ID does not exist"})


# TODO Get -> GET all Owner
@app.route("/author", methods=["GET"])
def get_Allauthor():
    name_contains = request.get.args("name_contains", type=str)
    query = author.query
    if name_contains:
        query = query.filter(author.name.ilike(f"%{name_contains}%"))

    authorlist = query.all()
    return jsonify(
        {
            "name": authorlist.name,
            "Wrote": len(authorlist.book),
            "book": [
                {
                    "title": Book.title,
                    "price": Book.price,
                }
                for Book in (authorlist.book)
            ],
        }
    )


# TODO Get -> GET Owner by id
@app.route("/author/<int:id>", methods=["GET"])
def get_author(id):
    Author = author.query.get(id)
    return jsonify(
        {
            "name": Author.name,
            "book": [
                {
                    "title": Book.title,
                    "price": Book.price,
                }
                for Book in (Author.book)
            ],
        }
    )


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
    return jsonify({"Sucess": f"Book added"})


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
    return jsonify({"UPDATE": f"Data at ID {Book.id} UPDATEd"})


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
        return jsonify({"UPDATE": f"Data at ID {Book.id} UPDATEd"})
    else:
        return jsonify({"error": "Book ID did not find "}), 404


# TODO Delete -> Delete data by id
@app.route("/shelf/book/<int:id>", methods=["DELETE"])
def DELETE_book(id):
    Book = books.query.get(id)
    if Book:
        db.session.delete(Book)
        db.session.commit()
        return jsonify({"DELETE": "Id deleted successfully!"})
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


@app.route("/person", methods=["POST"])
def create_person():
    data = request.get_json()
    Books = books.query.get(data["book_id"])
    if Books is None:
        return jsonify({"Error": "Book does not exist"}), 404
    Person = person(
        name=data["name"],
        profession=data["profession"],
        book_id=data["book_id"],
    )
    db.session.add(Person)
    db.session.commit()
    return jsonify({"Success": "Person added"})
