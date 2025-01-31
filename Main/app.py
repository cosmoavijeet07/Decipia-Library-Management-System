from flask import Flask
from model import db, User, bcrypt, login_manager
from api import api
from config import DevelopmentConfig
from flask_cors import CORS
from auth import auth
from lib import lib
from user import user


def create_app():
# Create a Flask app
    app = Flask(__name__)  # 
    app.config.from_object(DevelopmentConfig)
    db.init_app(app)
    api.init_app(app)
    app.register_blueprint(lib, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(user, url_prefix='/')
    app.app_context().push()
    
    bcrypt.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = "info"
    login_manager.init_app(app)
    
    return app

#Initiating APP
app = create_app()

CORS(app)


#Creating admin
with app.app_context():
    db.create_all()
    if User.query.filter_by(username='librarian').first() is None:  # Check if admin exists
            admin_user = User(
                username='librarian',
                email='librarian@gmail.com',
                roles='librarian'
            )
            admin_user.password = 'librarian'  
            db.session.add(admin_user)
            db.session.commit()
        

# Run the app if this file is executed
if __name__ == '__main__':
    app.run(debug=True, port=5001)
