from extension import db
from models import Users, TokenBlockList
from extension import bcrypt
from datetime import timedelta
from flask_mail import Message
from extension import mail
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token, 
                                get_jwt, get_jwt_identity, 
                                jwt_required, decode_token)


auth_bp= Blueprint('auth', __name__)

#done
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
            expires_delta= timedelta(minutes= 30))
    
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
        return jsonify({"msg":" Check your email for verfication code", "link": verification_link}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg":"Something went wrong during signup"}), 400
        

#done
@auth_bp.post('/verify-email/<token>')
def verification(token):
    try:
        
        if not token:
            return jsonify({"msg":"Token not found"}), 404
        try:
            decoded= decode_token(token)
            if decoded.get('token_type') != "email_verify":
                return jsonify({"msg":"Invalid or missing token "}), 400
        
            user_id= decoded.get('sub')
        
        except Exception:
            db.session.rollback()
            return jsonify({"msg":"Invalid or expired token"}), 400
    
        user= Users.query.get(user_id)
        
        if not user:
            return jsonify({ "msg":"User not found"}), 404
        
        if user.email_verified:
            return jsonify({"msg":"Email already verified"}), 403
        
        user.email_verified= True
        db.session.commit()
        return jsonify({"msg":"Email verification successfull"}), 200   
    except Exception as e:
        return str(e)

        
#done
@auth_bp.post('/login')
def login():
    try:
        data= request.json
        
        email= data.get("email", "").strip().lower()
        password= data.get("password", "").strip()
        
        user= Users.query.filter_by(email= email).first()
        
        if not user or not bcrypt.check_password_hash(user.password, password): 
            return jsonify({"msg": "Wrong user name or password"}), 401
        
        if user.email_verified == False:
            return jsonify({"msg":"Please verify your email "}), 401
        
        access_token= create_access_token(identity= user.id)
        refresh_token= create_refresh_token(identity= user.id)
    
        return jsonify({"Token": {
            "access token": access_token,
            "refersh token": refresh_token
        }}), 200
    except Exception as e:
        return str(e)
   

#done
@auth_bp.post('/forget_password')
@jwt_required(optional= True)
def forget_password():
    try:
        email= request.json.get("email", "").lower().strip()
        
        user= Users.query.filter_by(email= email).first()
        
        if not user:
            return jsonify({"msg":"User not found"}), 404
        
        reset_password_token= create_access_token(
            identity= user.id,
            additional_claims= {"token_type":"password_reset"},
            expires_delta= timedelta(minutes= 30))
        
        """verification_link= f"http://127.0.0.1:5000/auth/password_reset/{reset_password_token}""" #will still remove this part
        
        msg= Message(
            subject= 'Password reset',
            recipients= [user.email],
            html= f'''
            Hello, <br/>

            Click the link below to verfy your email and reset your password: <br/>
            <a href="{reset_password_token}">Click here to verify email</a>
            
            <br/> <br/>
            please ignore if you did not request for this mail
        #     '''
        )
        mail.send(msg)
        return jsonify({"msg":" Check your email for verfication code", "link": reset_password_token}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"msg":"Something went wrong "}), 400
    
#done
@auth_bp.patch('/password_reset')
@jwt_required(optional= True)
def reset_password():
    try:
        token= request.json.get("token")
        decode= decode_token(token)
        
        if not token or decode.get("token_type") != "password_reset":
            return jsonify({"msg":"Invalid or missing token "}), 400
        
        new_password= request.json.get("password", "").strip()
        
        if not new_password:
            return jsonify({"msg":"Please add a new password"}), 400
        
        if len(new_password) < 6:
            return jsonify({"msg":"Password must not be less than 6 "}), 403
        
        try:
            decoded= decode_token(token)
            user_id= decoded.get('sub')
        
        except Exception:
            db.session.rollback()
            return jsonify({"msg":"Invalid or expired token"}), 400
    
        user= Users.query.get(user_id)
        
        if not user:
            return jsonify({ "msg":"User not found"}), 404
    
        user.password= bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        return jsonify({"msg":"Password reset successfully"}), 200
    except Exception as e:
        return str(e)
  
  
#done  
@auth_bp.post('/refresh_token')
@jwt_required(refresh=True)
def refresh_token():
    identity= get_jwt_identity()
    
    new_access_token= create_access_token(identity= identity)
    return jsonify({"access token": new_access_token})
    
#done
@auth_bp.post('/logout')
@jwt_required()
def logout():
    identity= get_jwt()
    
    jti= identity.get('jti')
    
    revoke_token= TokenBlockList(jti= jti)
    
    db.session.add(revoke_token)
    db.session.commit()
    return jsonify({"msg": "Logout successfull"}), 200

#done
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

