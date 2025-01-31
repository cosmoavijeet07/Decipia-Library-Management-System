from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from flask_login import UserMixin, LoginManager
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
login_manager = LoginManager()

ist = timezone('Asia/Kolkata')

db = SQLAlchemy()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    roles = db.Column(db.String(100), nullable=False, default="user")
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    requested_books = db.relationship('RequestedBook', back_populates='user', lazy=True, cascade="all, delete-orphan")
    
    @property
    def password(self):
        raise AttributeError("password: write-only field")

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

# Define Section model
class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    books = db.relationship('Book', backref='section', lazy='dynamic', cascade="all, delete-orphan")

# Define Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(), nullable=True)
    releasedate = db.Column(db.DateTime, default=datetime.now(ist))
    price = db.Column(db.Integer, nullable=False)
    pdf = db.Column(db.String(511), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    requests = db.relationship('RequestedBook', backref='book', lazy='dynamic', cascade="all, delete-orphan")
    feedbacks = db.relationship('Feedback', backref='book', lazy='dynamic', cascade="all, delete-orphan")

class RequestedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_time = db.Column(db.DateTime, default=datetime.now(ist))
    deadline = db.Column(db.DateTime, nullable=True)
    issue_time = db.Column(db.DateTime, nullable=True)
    is_revoke = db.Column(db.Boolean, default=False)
    requested = db.Column(db.Boolean, default=True )
    is_issue = db.Column(db.Boolean, default=False)
    is_return = db.Column(db.Boolean, default=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='requested_books')
        
# Define Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
