
import os
from logger import logger
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask import Flask, jsonify
from routes import user, payment, admin, product, cart, order, auth, review
from datetime import timedelta
from models import Users, TokenBlockList
from extension import db, mail, bcrypt, jwt 




load_dotenv()


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
    app.config['JWT_ACCESS_TOKEN_EXPIRES']= timedelta(minutes= 10)
    app.config['JWT_REFRESH_TOKEN_EXPIRES']= timedelta(days= 7)
    #always keep secret keys hidden for safety
    app.config['SECRET_KEY']= os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY']= os.getenv('JWT_SECRET_KEY')
   
   
    
    logger.info('Application started')
    
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    
    migrate= Migrate(app, db)
    
    
    app.register_blueprint(review.review_bp, url_prefix= '/reviews')
    app.register_blueprint(auth.auth_bp, url_prefix= '/auth')
    app.register_blueprint(cart.cart_bp, url_prefix= '/carts')
    app.register_blueprint(order.order_bp, url_prefix= '/orders')
    app.register_blueprint(user.user_bp, url_prefix= '/users')
    app.register_blueprint(admin.admin_bp, url_prefix= '/admin')
    app.register_blueprint(payment.payment_bp, url_prefix= '/payments')
    app.register_blueprint(product.product_bp, url_prefix= '/products')
    
    
    @app.errorhandler(Exception) 
    def handle_exception(error):
        app.logger.error(f"Unhandled Exception {error}")
        return jsonify({"msg":"An unexpected error occured"}), 500
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity= int(jwt_data['sub'])
        return db.session.get(Users, identity)
    

    @jwt.additional_claims_loader
    def user_additional_claims_callback(user_id):
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
        logger.error('Error occurred', exc_info=True)
        return jsonify({"msg": "Somthing went wrong"}), 400
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.error('Error occurred', exc_info=True)
        return jsonify({"msg": "Somthing went wrong"}), 400
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logger.error('Error occurred', exc_info=True)
        return jsonify({"msg": "Something went wrong"}), 401
    
    return app



