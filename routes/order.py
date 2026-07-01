import uuid
from extension import db
from logger import logger
from flask import request, jsonify, Blueprint
from flask_jwt_extended import current_user, jwt_required, get_jwt_identity, get_jwt
from models import (Profiles, Categories, Products, Orders, OrderItems, Carts, CartItems, Reviews)





order_bp= Blueprint('orders', __name__)



@order_bp.post('/orders/create')
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
                reference= str(uuid.uuid4())
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
            
            user_id= get_jwt() 
            
            cart= Carts.query.filter_by(user_id= user_id).first()
            db.session.delete(cart)
            db.session.commit()
            
        return jsonify({"msg":"Order added"}), 201
    except Exception:
        logger.error("Error occured", exc_info=True)
        return jsonify({"msg":"Something went wrong"}), 400
   

@order_bp.post('/orders/revoke/<int:order_id>') 
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


@order_bp.post('/items/revoke/<int:item_id>') 
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


 