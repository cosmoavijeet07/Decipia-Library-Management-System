from flask import Flask, request, current_app, send_from_directory, abort, flash, redirect, url_for
from flask import render_template, Blueprint
from model import db, ist, bcrypt,  User as userdata, Section as sectiondata, Book as bookdata, RequestedBook as requestdata, Feedback as feedbackdata
from forms import Sign_in, log_in, UserProfileForm, FeedbackForm
from datetime import datetime
from sqlalchemy import and_, or_
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename, safe_join
import os

user = Blueprint('user', __name__)

@user.route('/')
def home():
    return render_template('home.html')


@user.route('/userdashboard', methods=['GET', 'POST'])
@login_required
def userdashboard():
    current_user_id = current_user.id
    user = current_user

    # Subquery to exclude books that are requested or issued by the user
    subquery = db.session.query(requestdata.book_id).filter(
        requestdata.user_id == current_user_id,
        or_(requestdata.requested == True, requestdata.is_issue == True)
    ).subquery()

    # Initial query to display all books and sections
    books = bookdata.query.outerjoin(subquery, bookdata.id == subquery.c.book_id).filter(
        subquery.c.book_id.is_(None)
    )
    sections = sectiondata.query.all()

    if request.method == 'POST':
        search_query = request.form.get('search_query')

        # Search for sections and books as per the user input
        books = bookdata.query.filter(
            bookdata.id.notin_(subquery),
            or_(
                bookdata.title.ilike(f"%{search_query}%"),
                bookdata.author.ilike(f"%{search_query}%")
            )
        ).all()
        sections = sectiondata.query.filter(
            sectiondata.title.ilike(f"%{search_query}%")
        ).all()

    return render_template('userdashboard.html', user=user, sections=sections, books=books, search_query=search_query if request.method == 'POST' else "")

##################################################################

@user.route('/requestbook/<int:book_id>', methods=['POST'])
@login_required
def requestbook(book_id):
    
    # Check the number of active requests by the current user
    active_requests_count = requestdata.query.filter_by(
        user_id=current_user.id,
        requested=True
    ).count()

    # Enforce the maximum limit of 5 active requests
    if active_requests_count >= 5:
        flash('You have reached the maximum limit of 5 active book requests.')
        return redirect(url_for('user.userdashboard'))

    # Check if the book is already requested or issued by the current user
    existing_request = requestdata.query.filter_by(
        book_id=book_id,
        user_id=current_user.id,
    ).filter(
        or_(requestdata.requested == True, requestdata.is_issue == True)
    ).first()

    if existing_request:
        flash('You have already requested or issued this book.')
        return redirect(url_for('user.userdashboard'))

    # Check if the book exists
    book = bookdata.query.get(book_id)
    if not book:
        flash('Book not found.')
        return redirect(url_for('user.userdashboard'))

    new_request = requestdata(user_id = current_user.id, book_id = book_id)
    new_request.requested = True
    new_request.is_issue = False

    # Save the new request to the database
    db.session.add(new_request)
    db.session.commit()

    flash('Book request submitted successfully.')
    return redirect(url_for('user.userdashboard'))

#########################################################################

@user.route('/availablebooks')
@login_required
def availablebooks():
    # Query to get all books issued by the current user
    issued_books = requestdata.query.filter(
        requestdata.user_id == current_user.id,
        requestdata.is_issue == True,
        requestdata.is_revoke == False,
        requestdata.is_return == False
    ).join(bookdata, requestdata.book_id == bookdata.id).all()

    # Prepare a list of books from the issued_books query
    books = [requested_book.book for requested_book in issued_books]

    # Logic to display available books
    return render_template('availablebooks.html', user=current_user, books=books, issued_books=issued_books)

###############################################################################

@user.route('/readbook/<int:book_id>', methods=['GET', 'POST'])
@login_required
def readbook(book_id):
    book = bookdata.query.get_or_404(book_id)
    feedback_submitted = feedbackdata.query.filter_by(book_id=book_id, user_id=current_user.id).first()
    form = FeedbackForm()
    
    if form.validate_on_submit() and request.method == 'POST' :
        if not feedback_submitted:
            # Only allow feedback if none has been submitted by this user for this book
            new_feedback = feedbackdata(
                user_id=current_user.id,
                book_id=book_id,
                feedback=form.feedback.data
            )
            db.session.add(new_feedback)
            db.session.commit()
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('user.readbook', book_id=book_id))
        else:
            flash('You have already submitted feedback for this book.', 'success')

    return render_template('readbook.html', book=book, form=form, feedback_submitted=feedback_submitted)

#####################################################################

@user.route('/download/<filename>')
@login_required
def downloadfile(filename):
    # Secure the filename to prevent directory traversal
    filename = secure_filename(filename)
    
    # Construct the full file path securely
    file_path = safe_join(current_app.config['UPLOAD_FOLDER_PDF'], filename)

    # Check if file exists
    if not os.path.exists(file_path):
        abort(404, description="File not found")

    # Send the file from the secured directory
    return send_from_directory(directory=current_app.config['UPLOAD_FOLDER_PDF'],path = file_path, filename=filename, as_attachment=True)

########################################################################

@user.route('/requestedbooks')
@login_required
def requestedbooks():
    # Query to get all books requested by the current user
    user_requests = requestdata.query.filter_by(
        user_id=current_user.id,
        requested=True  # Ensuring we're only getting the books that are still requested
    ).all()

    # Prepare a list of book details, taking into account the new 'issue_time' field
    requested_books = []
    for request in user_requests:
        book = bookdata.query.get(request.book_id)
        requested_books.append({
            'title': book.title,
            'author': book.author,
            'request_time': request.request_time.strftime('%Y-%m-%d %H:%M:%S'),
            'issue_time': request.issue_time.strftime('%Y-%m-%d %H:%M:%S') if request.is_issue else 'Not issued yet',
            'deadline': request.deadline.strftime('%Y-%m-%d %H:%M:%S') if request.is_issue else 'Not issued yet',
            'status': 'Issued' if request.is_issue else 'Requested'
        })

    # Logic to display requested books
    return render_template('requestedbooks.html',user = current_user, requested_books=requested_books)

###############################################################################

@user.route('/viewsection/<int:section_id>')
@login_required
def viewsection(section_id):
    # Logic to view a specific section
    section = sectiondata.query.get(section_id)
    return render_template('viewsection.html',user=current_user, section=section)

############################################################################
@user.route('/userprofile', methods=['GET', 'POST'])
@login_required
def userprofile():
    form = UserProfileForm()
    
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_username = form.new_username.data
        new_password = form.new_password.data

        # Verify current password
        if not current_user.check_password_correction(current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('user.userprofile'))

        # Update username if provided and different
        if new_username and new_username != current_user.username:
            current_user.username = new_username
            db.session.commit()
            flash('Your username has been updated.', 'success')

        # Update password if provided
        if new_password:
            current_user.password = new_password
            db.session.commit()
            flash('Your password has been updated.', 'success')

        return redirect(url_for('user.userprofile', user=current_user))

    return render_template('userprofile.html', user=current_user, form=form)

########################################################################################

@user.route('/returnbook/<int:book_id>')
@login_required
def returnbook(book_id):
    # Logic to mark a book as returned
    book_request = requestdata.query.filter_by(book_id=book_id, user_id=current_user.id, is_issue=True, is_return=False).first()
    if not book_request:
        flash('No active issue found for this book or book does not exist.', 'error')
        return redirect(url_for('user.availablebooks'))
    
    book_request.is_return = True
    book_request.is_issue = False
    book_request.requested = False# Mark the book as returned
    db.session.commit()
    flash('Book returned successfully!', 'success')
    return redirect(url_for('user.availablebooks'))

##############################################################################
                           
    