
from flask_mail import Mail
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy




db= SQLAlchemy()
mail= Mail()
jwt= JWTManager()
bcrypt= Bcrypt()
load_env_files= load_dotenv()
