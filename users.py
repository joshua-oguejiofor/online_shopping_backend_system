import os
import hashlib
import hmac
import requests
from uuid import uuid4
from extension import db
from logger import logger
from flask import request, jsonify, Blueprint
from flask_jwt_extended import current_user, jwt_required, get_jwt_identity
from models import (Profiles, Categories, Products, Orders, OrderItems, Carts, CartItems, Reviews)


user_bp= Blueprint('user', __name__)

    
PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")


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

 
@user_bp.get('/products/get')
@jwt_required(optional= True) #optional: for cases where users don't have account 
def get_all_products():
    
    page= request.args.get('page', default= 1, type= int)
    content_per_page= request.args.get('content_per_page', default= 10, type= int)
    
    product= Products.query.paginate(
        page= page,
        per_page= content_per_page,
        error_out= False
    )
    if not product.items:
        return jsonify({ "msg":"Page not found"}), 404
    
    return jsonify({
        "Products": [{
                "name":p.name,
                "description":p.description,
                "price":p.price
            }for p in product.items]
    }), 200

    
@user_bp.get('/products/<int:product_id>')
@jwt_required()
def get_product_by_id(product_id):
    
    product= Products.query.get(product_id)
    if not product:
        return jsonify({ "msg": "Product not found"}), 404
    
    return {
            "name": product.name,
            "description": product.description,
            "price":product.price,
            "stock": product.stock,
        }  
       

@user_bp.get('/products/categories')
@jwt_required()
def get_product_by_category():
    category= request.json.get("category","").strip().lower()
    page= request.args.get("page", 1, type= int) 
    
    categories= Categories.query.filter_by(name= category).first()
    
    if not categories:
        return jsonify({"msg": "Category not found"}), 404
    
    product= Products.query.filter_by(category_id= categories.id).order_by(Products.id.desc()).paginate(
        page= page,
        per_page= 10,
        error_out= False
    )
    if not product.items:
        return jsonify({ "msg": "No products for this category"}), 404
    
    return jsonify({
        "Products":[
            {
            "category": categories.name,
            "product name": p.name,
            "description": p.description,
            "price": p.price,
            "stoke": p.stock
            } for p in product.items
            ]}), 200
    
    
@user_bp.post('/products/search')
@jwt_required()
def search_product():
    name= request.json.get("name", "").strip().lower()
    page= request.args.get("page", 1, type= int)
    
    if not name:
        return jsonify({"msg":"Add a name to search"}), 400
    
    products= Products.query.filter(Products.name.ilike(f"%{name}%")).order_by(Products.id.desc()).paginate(
        page= page,
        per_page= 10,
        error_out= False
    )
    if not products.items:
        return jsonify({"msg":f"{name} did not match any product"}), 404
    
    return jsonify({
        "products":[
            {
            "product name": p.name,
            "description": p.description,
            "price": p.price,
            "stoke": p.stock
            } for p in products.items
            ]}), 200


'''CRUD for user_cart'''
@user_bp.post('/carts/create')
@jwt_required()
def add_to_cart():
    
    data= request.json 
    product_id= data.get("product_id","").strip()
    quantity= int(data.get("quantity",1))
    
    product= Products.query.get(int(product_id))
    
    if not product:
        return jsonify({"msg":"Product not found"}), 404
    
    if product.stock < quantity: 
        return jsonify({"msg":"Not enough product"}), 403
    
    cart= Carts.query.filter_by(user_id= current_user.id).first()
    if not cart:
        cart= Carts(user_id= current_user.id)
        db.session.add(cart)
        db.session.flush()
    
    cart_items= CartItems.query.filter_by(cart_id= cart.id, product_id= product_id).first()
    if cart_items:
        cart_items.quantity += quantity
        
    else:
        cart_items= CartItems(
            cart_id= cart.id,
            product_id= product.id,
            product_name= product.name,
            price= product.price,
            quantity= quantity    
        )
        db.session.add(cart_items)    
    db.session.commit() 
    return jsonify({"msg": "Product added to cart"}), 201


@user_bp.get('/carts/items')
@jwt_required()
def get_cart_items():
    
    cart= Carts.query.filter_by(user_id= current_user.id).first()      
    if not cart:
        return jsonify({"msg": "No cart created, add a product to cart to create one."}), 404
    
    cart_items= CartItems.query.filter_by(cart_id= cart.id).all()
    
    if not cart_items:
        return jsonify({"msg": "No item in cart."}), 404 #extra security
    
    total= 0
        
    subtotal= sum(items.price * items.quantity for items in cart_items)
    total += subtotal
        
    return jsonify({
        "items":[
            {
            "name": item.product_name,
            "price": item.price,
            "quantity":item.quantity, 
            } for item in cart_items],
        
            "total": len(cart_items),
            "total price": total
        }), 200
    
   
@user_bp.patch('/carts/update/<int:item_id>')
@jwt_required()
def update_cart_item(item_id):
    try:
        cart_items= CartItems.query.get(item_id)
        if not cart_items:
            return jsonify({"msg":"Item not found in cart"}), 404
        
        new_quantity= int(request.json.get("quantity", cart_items.quantity).strip())
        
        cart_items.quantity= new_quantity
        db.session.commit()
      
        return jsonify({"msg":"Updated successfully"}), 200
        
    except ValueError:
        return jsonify({"msg":"please add a number for quantity needed"}), 400

    
@user_bp.delete('/carts/remove/<int:item_id>')
@jwt_required()
def remove_from_cart(item_id):
    
    cart_item= CartItems.query.get(item_id)
    
    if not cart_item:
        return jsonify({"msg":"Item no longer in cart"}), 404
    
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"msg":"Item removed from cart"}), 200
    

@user_bp.post('/orders/create')
@jwt_required()
def create_order():
    try:
        with db.session.begin():
    
            data= request.json
            items= data.get('items')
            address= data.get('address', "").strip().lower()
            
            if not items or not isinstance(items, list):
                return jsonify({"msg":"Invalid data for order creation"}), 400
            
            if not address:
                return  jsonify({"msg":"Please add a location for order delivery"}), 400
            
            total= 0
            order_item_object= []
            
            for item in items:
                product_id= item.get('product_id')
                quantity= int(item.get('quantity'))
                
                
                if not product_id or not isinstance(quantity, int) or quantity <= 0:
                    return jsonify({"msg": "Invalid product data"}), 400

                product= Products.query.get(product_id)
                
                if not product:
                    return jsonify({"msg":f"Product with id '{product_id}' not available"}), 404
                    
                if product.stock < quantity:
                    return jsonify({"msg": f"Not enough stock for {product.name}"}), 403
                
                total += product.price * quantity
                
                order_item_object.append({
                    "quantity": quantity,
                    "price": product.price,
                    "product_id": product.id,
                    "product_name": product.name
                })
                
            order= Orders(
                user_id= current_user.id,
                
                total_amount= total,
                delivery_address= address,
                reference= str(uuid4())
            )
            db.session.add(order)
            db.session.flush()
            
            for oi in order_item_object:
                order_items= OrderItems(
                    order_id= order.id,
                    product_id= oi['product_id'],
                    product_name= oi['product_name'],
                    quantity= oi['quantity'],
                    price= oi['price']
                )
                db.session.add(order_items)
                
            product.stock -= quantity  
        return jsonify({"msg":"Order added"}), 201
    except Exception:
        logger.error("Error occured", exc_info=True)
        return jsonify({"msg":"Something went wrong"}), 400
   

@user_bp.post('/orders/revoke/<int:order_id>') 
@jwt_required()
def revoke_order(order_id):
    
        order= Orders.query.filter_by(id= order_id, user_id= current_user.id).first()
        if not order:
            return jsonify({"msg": "Order not found in the server"}), 404
        
        order_items= OrderItems.query.filter_by(order_id= order.id).all()
        
        for items in order_items:
        
            product= Products.query.get(items.product_id)
            product.stock += int(items.quantity)
            items.revoked= True
            
        order.revoked= True
        db.session.commit()
        return jsonify({"msg":"Order has been revoken successfully"}), 200


@user_bp.post('/items/revoke/<int:item_id>') 
@jwt_required()
def revoke_order_item(item_id):  
    
    order_items= OrderItems.query.get(item_id)
    if not order_items:
        return jsonify({"msg": "Item not found among order items"}), 404
    
    product= Products.query.get(order_items.product_id)
    product.stock += int(order_items.quantity)
    
    order_items.revoked= True
    db.session.commit()
    return jsonify({"msg": f"item {order_items.name} revoked successfully"}), 200


"""Paystack payment flow"""
@user_bp.post("/initialize_payment/<int:order_id>")
@jwt_required()
def initialize_payment(order_id):
    
    order= Orders.query.filter_by(id= order_id, user_id= current_user.id)
    if not order:
        return jsonify({"msg": "No order for payment"}), 404
    
    data = request.json
    email= data.get("email", "").lower().strip()
    amount= int(order.total_amount)
    
    if not email or email != current_user.email :
        return  jsonify({"msg": "Please enter a valid email to complete this payment"}), 400
        
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}",
               "content-type":"application/json"
    }
    payload = {
        "email": email,
        "amount": str(amount  * 100), # amount in kobo since paystack uses kobo for transactions and accept it as string
        "reference": order.reference
    }
    res = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    return jsonify(res.json())


@user_bp.get("/verify_payment")
def verify_payment():
    reference = request.args.get("reference")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    return jsonify(res.json())


@user_bp.post('/payments/webhook')
def paystack_webhook():
    payload= request.get_data()
    signature= request.headers.get("x-paystack-signature")
    
    computed_signature= hmac.new(
        PAYSTACK_SECRET.encode(),
        payload,
        hashlib.sha512        
    ).hexdigest
    
    if not hmac.compare_digest(computed_signature, signature):
        return jsonify({"msg":"Invalid signature"}), 400
    data= request.json
    event= data.get("event", "").strip()
    
    if event == "charge.success": 
        reference= data['data']['reference']
        
        order= Orders.query.filter_by(reference= reference).first()
        
        if order:
            order.status= "paid"
            db.session.commit()
    return "", 200

 
@user_bp.post('/reviews')
@jwt_required()
def reviews():
    data= request.json
    product_name= data.get("name", "").lower().strip()
    rating= int(data.get("rating", 0))
    comment= data.get("comment","").lower().strip()
    
    if not product_name or not comment:
        return jsonify({"msg":"Add a product name and your comment so we can improve in our service to you."}), 400
    
    order_item= OrderItems.query.filter_by(product_name= product_name).first()
    
    if not order_item:
        return jsonify({"msg":f"product of {product_name} did not match product delivered"}), 404
    
    reviews= Reviews(
            user_id= current_user.id,
            order_id= order_item.order_id,
            product_id= order_item.product_id,
            product_name= order_item.product_name,
            rating= rating,
            comment= comment
        )
    db.session.add(reviews)
    db.session.commit()
    return jsonify({"msg":"review received"}), 200

