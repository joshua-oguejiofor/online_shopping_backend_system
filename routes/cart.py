
from extension import db
from models import Products, Carts, CartItems
from flask import request, jsonify, Blueprint
from flask_jwt_extended import current_user, jwt_required




cart_bp= Blueprint('carts', __name__)





'''CRUD for user_cart'''
@cart_bp.post('/carts/create')
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


@cart_bp.get('/carts/items')
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
    
   
@cart_bp.patch('/carts/update/<int:item_id>')
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

    
@cart_bp.delete('/carts/remove/<int:item_id>')
@jwt_required()
def remove_from_cart(item_id):
    
    cart_item= CartItems.query.get(item_id)
    
    if not cart_item:
        return jsonify({"msg":"Item no longer in cart"}), 404
    
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"msg":"Item removed from cart"}), 200
    