class Config(object):
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config): 
    DEBUG = True
    secret_key = 'okokokok'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///lib.db' 
    SECRET_KEY = "qwerty1234fjcjfc5###"
    SECURITY_PASSWORD_SALT = "qwerty12345@#$"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER_PDF= "static/books"