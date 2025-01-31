from flask import Flask, request, flash, redirect, url_for, get_flashed_messages
from flask import render_template, Blueprint
from model import db,  User as userdata
from forms import Sign_in, log_in
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route("/login" , methods=['GET', 'POST'])
def login():
    form = log_in()
    if request.method == 'POST':
        
        username_or_email = form.username_or_email.data
        password = form.password.data
        attempted_user = userdata.query.filter(userdata.email == username_or_email).first() or userdata.query.filter(userdata.username == username_or_email).first()
        if attempted_user:
            if attempted_user.check_password_correction(attempted_password=password):
                login_user(attempted_user, remember=True)
                flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
                return redirect(url_for('user.userdashboard'))
            else:
                flash('Incorrect Password! Please try again', category='danger')
        else:
            flash('Email not found!', category='danger')
    return render_template('login.html', form=form)
    
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.home'))

@auth.route("/signup", methods=['GET', 'POST'])
def signup():
    form = Sign_in()
    if request.method == 'POST':
            if form.validate_on_submit():
                user_to_create = userdata(username=form.username.data,
                                email=form.email_address.data,
                                password=form.password1.data)
                db.session.add(user_to_create)
                db.session.commit()
                login_user(user_to_create, remember=True)
                flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
                return redirect(url_for('user.userdashboard'))
            if form.errors != {}: #If there are not errors from the validations
                for err_msg in form.errors.values():
                    flash(f'There was an error with creating a user: {err_msg}', category='danger')
    return render_template('signup.html', form=form)

@auth.route("/adminlogin", methods=['GET', 'POST'])
def admin_login():
    form = log_in()
    if request.method == 'POST':
        username_or_email = form.username_or_email.data
        password = form.password.data
        attempted_user = userdata.query.filter(username_or_email == "librarian@gmail.com").first() or userdata.query.filter(username_or_email == "admin").first()
        if attempted_user:
            if attempted_user.check_password_correction(attempted_password=password):
                login_user(attempted_user, remember=True)
                flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
                return redirect(url_for('lib.admindashboard'))
            else:
                flash('Incorrect Password! Please try again', category='danger')
        else:
            flash('Unauthorised Acess, You are not Admin!!!', category='danger')
    return render_template('adminlogin.html', form=form)
    
