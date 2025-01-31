from flask import request, jsonify, abort
from flask_restful import Resource, Api
from model import db, Book as bookdata, Section as sectiondata
from forms import CreateBookForm, EditBookContentForm
from flask_login import login_required, current_user

api = Api()

class BookListAPI(Resource):
    @login_required
    def get(self):
        # Retrieve all books
        books = bookdata.query.all()
        return jsonify([book.serialize() for book in books])

    @login_required
    def post(self):
            # Add a new book
        form = CreateBookForm(request.form)
        if form.validate():
            new_book = bookdata(
                title=form.title.data,
                author=form.author.data,
                content=form.content.data,
                genre=form.genre.data,
                releasedate=form.release_date.data,
                price=form.price.data,
                pdf=form.pdf.data.filename if form.pdf.data else None
                )
            db.session.add(new_book)
            db.session.commit()
            return jsonify(new_book.serialize()), 201
        else:
            abort(400, 'Invalid data for creating a book')

class BookAPI(Resource):
    @login_required
    def get(self, id):
        # Retrieve a single book by id
        book = bookdata.query.get_or_404(id)
        return jsonify(book.serialize())

    @login_required
    def put(self, id):
        # Update a book
        book = bookdata.query.get_or_404(id)
        form = EditBookContentForm(request.form)
        if form.validate():
            book.title = form.title.data if form.title.data else book.title
            book.author = form.author.data if form.author.data else book.author
            book.content = form.content.data
            db.session.commit()
            return jsonify(book.serialize())
        else:
            abort(400, 'Invalid data for updating the book')

    @login_required
    def delete(self, id):
            # Delete a book
        book = bookdata.query.get_or_404(id)
        db.session.delete(book)
        db.session.commit()
        return jsonify({'message': 'Book deleted successfully'}), 204

api.add_resource(BookListAPI, '/api/books', endpoint='books')
api.add_resource(BookAPI, '/api/books/<int:id>', endpoint='book')

class SectionListAPI(Resource):
    @login_required
    def get(self):
        # Retrieve all sections
        sections = sectiondata.query.all()
        return jsonify([section.serialize() for section in sections])

    @login_required
    def post(self):
        # Add a new section
        data = request.get_json()
        new_section = sectiondata(
            title=data['title'],
            description=data.get('description', '')
        )
        db.session.add(new_section)
        db.session.commit()
        return jsonify(new_section.serialize()), 201

class SectionAPI(Resource):
    @login_required
    def get(self, id):
        # Retrieve a single section by id
        section = sectiondata.query.get_or_404(id)
        return jsonify(section.serialize())

    @login_required
    def put(self, id):
        # Update a section
        section = sectiondata.query.get_or_404(id)
        data = request.get_json()
        section.title = data['title']
        section.description = data.get('description', section.description)
        db.session.commit()
        return jsonify(section.serialize())

    @login_required
    def delete(self, id):
        # Delete a section
        section = sectiondata.query.get_or_404(id)
        db.session.delete(section)
        db.session.commit()
        return jsonify({'message': 'Section deleted successfully'}), 204

# Add these lines in the create_api function:
api.add_resource(SectionListAPI, '/api/sections', endpoint='sections')
api.add_resource(SectionAPI, '/api/sections/<int:id>', endpoint='section')
