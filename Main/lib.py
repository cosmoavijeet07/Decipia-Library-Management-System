from flask import Flask, request, flash, redirect, url_for, current_app
from flask import render_template, Blueprint
from model import db,ist,  User as userdata, Section as sectiondata, Book as bookdata, RequestedBook as requestdata, Feedback as feedbackdata
from forms import CreateSectionForm, CreateBookForm, EditBookContentForm
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os

lib = Blueprint('lib', __name__)

# Admin Dashboard route
@lib.route('/admindashboard')
@login_required
def admindashboard():
    books = bookdata.query.all()
    sections = sectiondata.query.all()
    users = userdata.query.all()
    return render_template('admindashboard.html', books=books, sections=sections, users=users)


ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for creating a book
@lib.route('/createbook', methods=['GET', 'POST'])
@login_required
def createbook():
    form = CreateBookForm()
    if form.validate_on_submit():
        if form.pdf.data:
            filename = secure_filename(form.pdf.data.filename)
            if not allowed_file(filename):
                flash('Only PDF files are allowed.', 'danger')
                return render_template('createbook.html', form=form)

            pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER_PDF'], filename)
            form.pdf.data.save(pdf_path)
        extisting_book = bookdata.query.filter_by(title = form.title.data).first()
        if extisting_book is not None:
            flash('Title already exists.', 'danger')
            return render_template('createbook.html', form=form)

        new_book = bookdata(
            title=form.title.data,
            author=form.author.data,
            content=form.content.data,
            genre=form.genre.data,
            releasedate=form.release_date.data,
            price=form.price.data,
            pdf=filename if form.pdf.data and allowed_file(filename) else None,
            section_id=form.section.data.id if form.section.data else None  # Handle section
        )
        db.session.add(new_book)
        db.session.commit()
        flash('New book created successfully!', 'success')
        return redirect(url_for('lib.admindashboard'))
    
    return render_template('createbook.html', form=form)

@lib.route('/editbook/<int:id>', methods=['GET', 'POST'])
@login_required
def editbook(id):
    book = bookdata.query.get_or_404(id)
    form = EditBookContentForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            book.content = form.content.data
            db.session.commit()
            flash('Book content updated successfully!', 'success')
            return redirect(url_for('lib.editbook', id=id))
        else:
            # Handling form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in the {getattr(form, field).label.text}: {error}", 'error')

    # On GET or failed validation, re-render the page
    form.content.data = book.content  # Prepopulate form with current content
    return render_template('editbook.html', form=form, book=book)

# Route for deleting a book
@lib.route('/deletebook/<int:id>')
@login_required
def deletebook(id):
    book = bookdata.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.')
    return redirect(url_for('lib.admindashboard'))

# Route for creating a section
@lib.route('/createsection', methods=['GET', 'POST'])
@login_required
def createsection():
    form = CreateSectionForm()
    if form.validate_on_submit():
        # Check if a section with the same title already exists to avoid duplicates
        existing_section = sectiondata.query.filter_by(title=form.title.data).first()
        if existing_section:
            flash('A section with that title already exists.', 'warning')
            return render_template('createsection.html', form=form)

        # Create new section and add to database
        new_section = sectiondata(title=form.title.data, description=form.description.data)
        db.session.add(new_section)
        db.session.commit()
        flash('New section created successfully!', 'success')
        return redirect(url_for('lib.admindashboard'))
    
    return render_template('createsection.html', form=form)

# Route for editing a section
@lib.route('/editsection/<int:id>', methods=['GET', 'POST'])
@login_required
def editsection(id):
    section = sectiondata.query.get_or_404(id)
    unassigned_books = bookdata.query.filter((bookdata.section_id == None) | (bookdata.section_id == id)).all()

    if request.method == 'POST':
        selected_book_ids = request.form.getlist('books')
        for book in unassigned_books:
            if str(book.id) in selected_book_ids:
                book.section_id = id
            elif book.section_id == id:
                book.section_id = None  # Remove the book from the section if unchecked
        db.session.commit()
        flash('Section updated successfully!', 'success')
        return redirect(url_for('lib.admindashboard'))

    return render_template('editsection.html', section=section, books=unassigned_books)

# Route for deleting a section
@lib.route('/deletesection/<int:id>')
@login_required
def deletesection(id):
    section = sectiondata.query.get_or_404(id)
    db.session.delete(section)
    db.session.commit()
    flash('Section deleted successfully.')
    return redirect(url_for('lib.admindashboard'))

@lib.route('/bookrequests')
@login_required
def bookrequests():
    requests = requestdata.query.filter_by(is_issue=False, requested = True).all()  # Only fetch unissued requests
    return render_template('bookrequests.html', requests=requests, current_time=datetime.now(ist))

@lib.route('/issuebook/<int:request_id>')
@login_required
def issuebook(request_id):
    request = requestdata.query.get_or_404(request_id)
    if not request.is_issue:
        request.is_issue = True
        request.is_revoke= False
        request.requested = False
        request.is_return = False
        request.issue_time = datetime.now(ist)
        request.deadline = request.issue_time + timedelta(days=7)
        db.session.commit()
        flash(f"Book issued successfully until {request.deadline}", "success")
    else:
        flash("This book has already been issued.", "info")
    return redirect(url_for('lib.bookrequests'))

# Route for viewing a user profile and their issued books
@lib.route('/viewuser/<int:id>')
@login_required
def viewuser(id):
    user = userdata.query.get_or_404(id)
    # Retrieve all books issued to the user that have not been revoked
    issued_books = requestdata.query.filter_by(user_id=id, is_issue=True, is_revoke=False).all()
    return render_template('viewuser.html', user=user, issued_books=issued_books)

@lib.route('/revokebook/<int:request_id>')
@login_required
def revokebook(request_id):
    book_request = requestdata.query.get_or_404(request_id)
    if book_request and not book_request.is_revoke:
        book_request.is_revoke = True
        book_request.requested = False
        book_request.is_issue = False
        book_request.is_return = False
        db.session.commit()
        flash('Access revoked successfully.', 'success')
    else:
        flash('No action taken or already revoked.', 'info')
    return redirect(url_for('lib.viewuser', id=book_request.user_id))




def update_expired_book_requests():
    """Update all expired book requests to set 'is_revoke' to True."""
    now = datetime.now(ist)
    expired_requests = requestdata.query.filter(
        requestdata.deadline <= now,  # Check if the deadline has passed
        requestdata.is_revoke == False  # Make sure it's not already revoked
    ).all()

    for request in expired_requests:
        request.is_revoke = True
    
    db.session.commit()  # Commit all changes at once

@lib.route('/updateexpiredbooks')
@login_required
def updateexpiredbooks():
    update_expired_book_requests()
    flash('All expired book requests have been updated.', 'success')
    return redirect(url_for('lib.admindashboard'))


import matplotlib.pyplot as plt
from io import BytesIO
import base64
from sqlalchemy import func
from flask import render_template, url_for

@lib.route('/adminstatistics')
@login_required
def adminstatistics():
    # Query to get the top 10 books based on the number of requests
    top_books = db.session.query(
        bookdata.title,
        func.count(requestdata.id).label('total_requests')
    ).join(requestdata, bookdata.id == requestdata.book_id
    ).group_by(bookdata.title
    ).order_by(func.count(requestdata.id).desc()
    ).limit(10).all()

    # Generate bar chart using Matplotlib
    books = [book[0] for book in top_books]  # Titles of books
    requests = [book[1] for book in top_books]  # Total requests per book
    plt.figure(figsize=(10, 6))
    plt.bar(books, requests, color='purple')
    plt.xlabel('Books')
    plt.ylabel('Number of Requests')
    plt.title('Top 10 Most Requested Books')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save plot to a bytes buffer and encode
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_url = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()


    # Additional statistics
    total_books = bookdata.query.count()
    total_users = userdata.query.count()
    total_issued_books = requestdata.query.filter_by(is_issue=True).count()
    total_requested_books = requestdata.query.filter_by(requested=True).count()
    total_sections = sectiondata.query.count()

    return render_template('statistics.html', 
                           total_books=total_books,
                           total_users=total_users,
                           total_issued_books=total_issued_books,
                           total_requested_books=total_requested_books,
                           total_sections=total_sections,
                           plot_url=plot_url)

