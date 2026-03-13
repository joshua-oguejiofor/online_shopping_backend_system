import random
from extension import db
from logger import logger
from models import Users, TokenBlockList, ForgetPassword
from extension import bcrypt
from datetime import timedelta
from flask_mail import Message
from extension import mail
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token, 
                                get_jwt, get_jwt_identity, current_user,
                                jwt_required, decode_token)


auth_bp= Blueprint('auth', __name__)

logger.info('Authentication app accessed')

@auth_bp.post('/signup')
def signup():
    
    try:
        data= request.json
        email= data.get("email", "").strip().lower()
        password= data.get("password", "").strip()
        
        if not email or not password :
            return jsonify({"msg": "Email or password cannot be empty"}), 400
        
        if len(password) < 6:
            return jsonify({"msg":" Password must not be less than 6"}), 400
        
        if '@' not in email:
            return jsonify({"msg":" Please add a valid email"}), 400
        
        if Users.query.filter_by(email= email).first():
            return jsonify({"msg": "This email has been registered"}), 403
            
        hashed_password= bcrypt.generate_password_hash(password).decode('utf-8')
        
        user= Users( email= email, password= hashed_password)
        db.session.add(user)
        db.session.commit()
        
        verify_token= create_access_token(
            identity= user.id,
            additional_claims= {"token_type":"email_verify"},
            expires_delta= timedelta(minutes= 10))
    
        verification_link= f"http://127.0.0.1:5000/auth/verify-email/{verify_token}"
        
        msg= Message(
            subject= 'Email verification',
            recipients= [email],
            html= f'''
            
            Hello, <br/>

            Click the link to verfy your email. <br/>
            <a href="{verification_link}">Click Here</a>
            
            <br/><br/>
            
            please ignore if you did not request for this mail
            '''
        )
        mail.send(msg)
        return jsonify({"msg":" Check your email for verfication details"}), 200
    except Exception:
        db.session.rollback()
        logger.error('error occurred', exc_info=True)
        return jsonify({"msg":"Something went wrong during signup"}), 400
        

@auth_bp.post('/verify-email/<token>')
def verification(token):
    logger.info('email verification endpoint accessed')
    try:
        
        if not token:
            return jsonify({"msg":"Token not found"}), 404
        try:
            decoded= decode_token(token)
            if decoded.get('token_type') != "email_verify":
                return jsonify({"msg":"Invalid or missing token "}), 400
        
            user_id= decoded.get('sub')
        
        except Exception:
            logger.error('error occurred', exc_info=True)
            return jsonify({"msg":"Something went wrong during signup"}), 400
        
        user= Users.query.get(user_id)
        
        if not user:
            return jsonify({ "msg":"User not found"}), 404
        
        if user.email_verified:
            return jsonify({"msg":"Email already verified"}), 403
        
        user.email_verified= True
        db.session.commit()
        return jsonify({"msg":"Email verification successfull"}), 200   
    except Exception:
        db.session.rollback()
        logger.error('error occurred', exc_info=True)
        return jsonify({"msg":"Something went wrong during signup"}), 400
        
        
@auth_bp.post('/login')
def login():
    logger.info('Login endpoint accessed')
    try:
        data= request.json
        
        email= data.get("email", "").strip().lower()
        password= data.get("password", "").strip()
        
        user= Users.query.filter_by(email= email).first()
        
        if not user or not bcrypt.check_password_hash(user.password, password): 
            return jsonify({"msg": "Invalid login details"}), 401
        
        if user.email_verified == False:
            return jsonify({"msg":"Email not verified "}), 401
        
        access_token= create_access_token(identity= user.id)
        refresh_token= create_refresh_token(identity= user.id)
    
        return jsonify({"Token": {
            "access token": access_token,
            "refersh token": refresh_token
        }}), 200
    except Exception:
        logger.error('error occurred', exc_info=True)
        return jsonify({"msg":"Something went wrong"}), 400


@auth_bp.patch('/change_password')
@jwt_required()
def reset_password():
    try:
        old_password= request.json.get("old_password", "").strip()
        new_password= request.json.get("new_password", "").strip()
        
        if not new_password or not old_password:
            return jsonify({"msg":"Password confirmation needed with both old and new password"}), 400
        
        if len(new_password) < 6:
            return jsonify({"msg":"Password must not be less than 6 "}), 400
        
        user_id= get_jwt_identity()
        user= Users.query.get(user_id)
        if not user:
            return jsonify({ "msg":"User not found"}), 404
        
        if not bcrypt.check_password_hash(user.password, old_password):
            return jsonify({"msg":"Incorrect old password"}), 400
            
        user.password= bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        return jsonify({"msg":"Password reset successfully"}), 200
    except Exception:
        logger.error("Error occurred", exc_info=True)
        return jsonify({"msg":"Somthing went wrong"}), 400
      
   
@auth_bp.post('/forget_password')
def forget_password():
    try:
        email= request.json.get("email", "").lower().strip()
        
        user= Users.query.filter_by(email= email).first()
        
        if not user:
            return jsonify({"msg":"Email not found"}), 404
        
        password_otp= f"{random.randint(0, 9999) :06d}"        
        
        msg= Message(
            subject= 'Password reset',
            recipients= [user.email],
            html= f'''
            Hello, 
            your password reset OTP {password_otp}
            do not share this with anybody.
            Note: the code expires in 5 minuties
            
            Please ignore if you did not request for this mail
            '''
        )
        mail.send(msg)
        
        forget_pwd= Users(password_otp= password_otp)
        db.session.add(forget_pwd)
        db.session.commit()
        
        return jsonify({"msg":" Check your email for verfication code"}), 200
    except Exception:
        logger.error('error occurred', exc_info=True)        
        return jsonify({"msg":"Something went wrong "}), 400


@auth_bp.post('/verify_otp')
def verify_otp():
    try:
        otp= int(request.json.get("otp", "").strip())
        
        code= Users.query.filter_by(password_otp= otp).first()
        if not code:
            logger.error('Invalid code access atempt', exc_info=True)
            return jsonify({"msg":"Something went wrong"}), 400
        
        return jsonify({"msg":"Otp verified"}), 200
    except ValueError:
        return jsonify({"msg":"Invalid code"}), 400
 

@auth_bp.post('/reset_password')
def reset_password():
    
    data= request.json
    email= data.get("email", "").strip()
    new_password= data.get("new_password", "").strip()
        
    if not new_password or email:
        return jsonify({"msg":"Email and password required"}), 400
    
    if len(new_password) < 6:
        return jsonify({"msg":"Password must not be less than 6 "}), 400
    
    user= Users.query.filter_by(email= email)
    if not user:
        return jsonify({ "msg":"User not found"}), 404
    
    user.password= bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return jsonify({"msg":"Password reset successfully"}), 200

  
@auth_bp.post('/refresh_token')
@jwt_required(refresh=True)
def refresh_token():
    identity= get_jwt_identity()
    
    new_access_token= create_access_token(identity= identity)
    return jsonify({"access token": new_access_token})
    

@auth_bp.post('/logout')
@jwt_required()
def logout():
    identity= get_jwt()
    
    jti= identity.get('jti')
    
    revoke_token= TokenBlockList(jti= jti)
    
    db.session.add(revoke_token)
    db.session.commit()
    return jsonify({"msg": "Logout successfull"}), 200


@auth_bp.post('/revoke_token')
@jwt_required(refresh= True)
def revoke_refresh_token():
    identity= get_jwt()
    
    jti= identity.get('jti')
    type= identity.get('type')
    
    revoke_token= TokenBlockList(jti= jti)
    
    db.session.add(revoke_token)
    db.session.commit()
    return jsonify({"msg":f"{type} token revoked"}), 200

