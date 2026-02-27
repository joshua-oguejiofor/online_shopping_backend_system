
import os
import logging
from extension import load_env_files
from logging.handlers import RotatingFileHandler
from flask_migrate import Migrate
from flask import Flask, jsonify
from users import user_bp
from admin import admin_bp
from datetime import timedelta
from authentication import auth_bp
from models import Users, TokenBlockList
from extension import db, mail, bcrypt, jwt







def create_app():
    app= Flask(__name__)
    

    #sqlalchemy configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI' )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('TRACK_MODIFICATIONS' , 'False') in [ 'False', 'false', '0']
   # mail configurations
    app.config['MAIL_SERVER']= os.getenv('MAIL_SEVER')
    app.config['MAIL_PORT']= int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS']= os.getenv('MAIL_USE_TLS', 'True') in ['True', 'true', '1']
    app.config['MAIL_USERNAME']= os.getenv('MAIL_USERNAME')
    app.config['MIAL_PASSWORD']= os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER']= os.getenv('MAIL_DEFAULT_SENDER')
    #tokens life cycles
    app.config['JWT_ACCESS_TOKEN_EXPIRES']= timedelta(days= 10)
    app.config['JWT_REFRESH_TOKEN_EXPIRES']= timedelta(days= 30)
    #always keep secret keys hidden for safety
    app.config['SECRET_KEY']= os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY']= os.getenv('JWT_SECRET_KEY')
   
   # logging configurations
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    file_handler= RotatingFileHandler(
    'logs/app.log',
    maxBytes= 10240,
    backupCount= 10
    )
    file_handler.setLevel(logging.INFO)
    formatter= logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application started')
    
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    
    migrate= Migrate(app, db)
    
    app.register_blueprint(auth_bp, url_prefix= '/auth')
    app.register_blueprint(user_bp, url_prefix= '/user')
    app.register_blueprint(admin_bp, url_prefix= '/admin')
    
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled Exception {error}")
        
        return jsonify({"msg":"An unexpected error occured"}), 500
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity= int(jwt_data['sub'])
        # return Users.query.get(identity)
        return db.session.get(Users, identity)
    

    @jwt.additional_claims_loader
    def user_additional_claims_callback(user_id):
        # user= Users.query.get(user_id)
        user= db.session.get(Users, user_id )
        return {"role": user.role, "status":user.status}
    
    @jwt.user_identity_loader
    def user_identity_callback(user_id):
        return str(user_id)
    
    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_data):
        jti= jwt_data.get('jti')
        return  TokenBlockList.query.filter_by(jti= jti).first() is not None
      
    #jwt error handlers 
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_date):
        return jsonify({"msg": "token_expired"}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"msg": "invalid token"}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"msg": "Unauthorization_header"}), 401
    
    return app



