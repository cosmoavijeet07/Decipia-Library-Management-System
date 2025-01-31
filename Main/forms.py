from flask_wtf import FlaskForm
from wtforms import TextAreaField, FileField, StringField, PasswordField, SubmitField, FileField, SelectField, DateField, IntegerField, SelectMultipleField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, Optional, NumberRange
from model import User, Section
from wtforms_sqlalchemy.fields import QuerySelectField

class Sign_in(FlaskForm):
    def validate_username(self, username_to_check):
        user = User.query.filter_by(username= username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different username')

    def validate_email_address(self, email_address_to_check):
        email_address = User.query.filter_by(email=email_address_to_check.data).first()
        if email_address:
            raise ValidationError('Email Address already exists! Please try a different email address')

    username = StringField(label='User Name:', validators=[Length(min=2, max=30), DataRequired()])
    email_address = StringField(label='Email Address:', validators=[Email(), DataRequired()])
    password1 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label='Confirm Password:', validators=[EqualTo('password1'), DataRequired()])
    submit = SubmitField(label='Create Account')
    
class log_in(FlaskForm):
    def validate_username(self, username_to_check):
        user = User.query.filter_by(username= username_to_check.data).first()
        if not user:
            raise ValidationError('Username does not exists! Please try a different username')

    def validate_email_address(self, email_address_to_check):
        email_address = User.query.filter_by(email=email_address_to_check.data).first()
        if not email_address:
            raise ValidationError('Email Address does not exists! Please try a different email address')

    username_or_email = StringField(label='username_or_email:', validators=[Length(min=2, max=30), DataRequired()])
    password = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='LogIn')
    
class UserProfileForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_username = StringField('New Username', validators=[Optional(), Length(min=2, max=50)])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    
class FeedbackForm(FlaskForm):
    feedback = TextAreaField('Your Feedback', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class CreateSectionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Create Section')
    
class CreateBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    author = StringField('Author', validators=[DataRequired(), Length(min=3, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    genre = SelectField('Genre', choices=[('Fiction', 'Fiction'), ('Non-fiction', 'Non-fiction'), ('Science', 'Science'), ('History', 'History')], validators=[Optional()])
    release_date = DateField('Release Date', format='%Y-%m-%d', validators=[Optional()])
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min=0)])
    pdf = FileField('PDF File', validators=[Optional()])
    section = QuerySelectField('Section', query_factory=lambda: Section.query.all(), get_label='title', allow_blank=True, blank_text='Select a section', validators=[Optional()])
    submit = SubmitField('Create Book')
    
class EditBookContentForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])