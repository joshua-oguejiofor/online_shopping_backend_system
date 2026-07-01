import os
from uuid import uuid4
from extension import db
from logger import logger
from flask import request, jsonify, Blueprint
from flask_jwt_extended import current_user, jwt_required, get_jwt_identity, get_jwt
from models import (Profiles, Categories, Products, Orders, OrderItems, Carts, CartItems, Reviews)


user_bp= Blueprint('users', __name__)

    


@user_bp.post('/profiles/create')
@jwt_required()
def create_profile():
    try:
        data= request.json
        
        first_name= data.get("first_name", "").strip().lower()
        last_name= data.get("last_name", "").strip().lower()
        raw_phone= data.get("phone", "").strip()
        address= data.get("address", "").strip().lower()
        country= data.get("country", "").strip().lower()
        
        if not first_name or not last_name or not raw_phone or not address or not country:
            return jsonify({"msg": "All fields are required complete your profile creation"}), 400
        
        if Profiles.query.filter_by(user_id= current_user.id).first():
            return jsonify({ "msg": "Profile already exist"}), 403
        
        phone= Profiles.number_format(raw_phone)
        if not (10 <= len(phone) <= 15):
            
            return jsonify({ "msg": """
                Please we only accept Nigerian numbers for now
                we hope to improve about this soon.
                """}), 400
        
        if Profiles.query.filter_by(phone= phone).first():
            return jsonify({ "msg": "Cannot accept a duplicate phone number"}), 403
        
        profile= Profiles( 
                        user_id= current_user.id,
                        first_name= first_name, 
                        last_name= last_name,
                        phone= phone,
                        address= address,
                        country= country
                        )
        db.session.add(profile)
        db.session.commit()
            
        return jsonify({"msg":"Profile created successfully"}), 201
    except Exception:
        logger.error("Error occured", exc_info=True)
        db.session.rollback()
        return jsonify({"msg":"Something went wrong during profile creation"}), 400


@user_bp.put('/profiles/update')
@jwt_required()
def update_my_profile():
    try: 
        user_id= get_jwt_identity()
        
        profile= Profiles.query.filter_by(user_id= user_id).first()
        if not profile:
            return jsonify({"msg": "Profile not found"}), 404
        
        data= request.json
        first_name= data.get("first_name",profile.first_name).strip().lower()
        last_name= data.get("last_name",profile.last_name).strip().lower()
        address= data.get("address",profile.address).strip().lower()
        country= data.get("country",profile.country).strip().lower()
        raw_phone= data.get("phone")
        
        if not raw_phone:
            profile.phone= profile.phone
            
        else:
            phone=  Profiles.number_format(raw_phone.strip())
            
            if not (10 <= len(phone) <= 15):
                return jsonify ({ "msg": """
                
                Please we only accept Nigerian numbers for now
                we hope to improve about this soon.
                """}), 400
                
            profile.phone= phone
                
        profile.first_name= first_name
        profile.last_name= last_name
        profile.address= address
        profile.country= country
        
        db.session.commit()
        return jsonify({"msg":"Profile updated"}), 200
    except Exception:
        logger.error("Error occured", exc_info=True)
        db.session.rollback()
        return jsonify({"msg":"Something went wrong while updating profile"}), 400


@user_bp.get('/profiles/view')
@jwt_required()
def view_my_profile():
    
    user_id= get_jwt_identity()
    
    profile= Profiles.query.filter_by(user_id= user_id).first()
    if not profile:
        return jsonify({ "msg": "Profile not found"}), 404
    
    return jsonify({
        "Profile":{
            "first name": profile.first_name,
            "last name": profile.last_name,
            "phone number": profile.phone,
            "address": profile.address,
            "country": profile.country    
        }}), 200    


