from extension import db
from flask import jsonify
from functools import wraps
from datetime import datetime
from flask import Blueprint, request, jsonify
from models import Categories, Products, Orders, Users, OrderItems
from flask_jwt_extended import get_jwt, verify_jwt_in_request


admin_bp= Blueprint('admin',__name__)

def admin_required(fn):
        @wraps(fn)
        def wrapper(*args, **kargs):
            
            verify_jwt_in_request()
            
            claims= get_jwt()

            if claims.get('role') != 'admin':
                return jsonify({"msg": "Only admin can access"}), 401
            return fn(*args, **kargs)
        return wrapper


def admin_or_vendor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        
        verify_jwt_in_request()
        
        role= get_jwt()
        
        if role.get('role') not in ['vendor', 'admin']:
            return jsonify({"msg":"Cannot access if not a vendor or an admin"}), 401
        
        if role.get("status")== "suspended":
            return jsonify({"msg":"Account has been suspended"}), 401
        
        return fn(*args, **kwargs)
    return wrapper
   
   

@admin_bp.get('/users/get')
@admin_required
def get_all_users():
    
    page= request.args.get('page', default= 1, type= int)
    content_per_page= request.args.get('content_per_page', default= 10, type= int)
    
    users= Users.query.paginate(
        page= page,
        per_page= content_per_page
    )
    
    return jsonify({
        "Users": [
        {
        "id": user.id,
        "role": user.role,
        "email": user.email,
        "status": user.status,
        "created_at": user.created_at,
        "verified": user.is_verified,
        }for user in users.items],
        
        "Total": users.total
        }), 200
    

@admin_bp.get('/users/<int:user_id>')
@admin_required
def get_user_by_id(user_id):
    
    user= Users.query.get(user_id)
    if not user:
        return jsonify({"msg":"user not found"}), 404
    
    return jsonify({
        "id": user.id,
        "role": user.role,
        "name": user.email,
        "status": user.status,
        "created_at": user.created_at,
        "verified": user.email_verified,
         }), 200

 
@admin_bp.get('/orders/get')
@admin_required
def get_all_orders():
    
    page= request.args.get('page', default= 1, type= int)
    content_per_page= request.args.get('content_per_page', default= 10, type= int)
    
    orders= Orders.query.paginate(

        page= page,
        per_page= content_per_page
    )
    if not orders.items:
        return ({"msg":"Page not found"}), 404
    
    return jsonify({
        "Oders": [
        {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "reference": order.reference,
        "status": order.status,
        "address": order.delivery_address,
        "created_at": order.created_at,
        "time_sent": order.time_sent,
        "received": order.time_received
        }for order in orders.items],
        "Total": orders.total
        }), 200
    

@admin_bp.get('/orders/items/<int:item_id>')
@admin_required
def get_order_item(item_id):
    
    order_item= OrderItems.query.get(item_id)
    
    if not order_item:
        return jsonify({"msg": "No items to display"}), 404
    
    return jsonify({"Item":
        {
            "id": order_item.id,
            "order_id": order_item.order_id,
            "product name": order_item.product_name,
            "price": order_item.price,
            "quantity": order_item.quantity   
        }}), 200
 
 
@admin_bp.post('/categories/create')
@admin_required  
def create_categories():
    data= request.json
    
    name= data.get("name", "").strip().lower()
    description= data.get("description", "").strip().lower()
    
    if not name or not description:
        return jsonify({"msg":"Please add a name or description for this category"}), 400
    
    category= Categories(name= name, description= description)
    
    db.session.add(category)
    db.session.commit()
    return jsonify({"msg": "Category created successfully"}), 201


@admin_bp.get('/categories/get')
@admin_or_vendor_required
def get_categories():
    
    page= request.args.get('page', default= 1, type= int)
    content_per_page= request.args.get('content_per_page', default= 10, type= int)
    
    categories= Categories.query.paginate(
        page= page,
        per_page= content_per_page
    )
    if not categories.items:
        return ({"msg":"Page not found"}), 404
    
    return jsonify({
        "Categories": [
        {
        "id": category.id,
        "category name": category.name,
        "description": category.description,
        }for category in categories.items],
        
        "Total": categories.total
        }), 200
     
    
@admin_bp.put('/categories/update/<int:category_id>')
@admin_required
def update_category(category_id):
    
    category= Categories.query.get(category_id)
    if not category:
        return jsonify({"msg": f"Category with id '{id}' not found"}), 404
    
    data= request.json
    name= data.get("name", category.name).strip().lower()
    description= data.get("description", category.description).strip().lower()
    
    category.name= name
    category.description= description
    db.session.commit()
    return jsonify({"msg":"Category updated successfully"}), 200


@admin_bp.delete('/categories/delete/<int:category_id>')
@admin_required
def delete_category(category_id):
    
    category= Categories.query.get(category_id)
    if not category:
        return jsonify({"msg": f"Category with id '{id}' not found"}), 404
    
    if Products.query.filter_by(category_id= category.id).first():
        return jsonify({"msg":"category still has products"}), 403
    
    db.session.delete(category)
    db.session.commit()
    return jsonify({"msg": "Deleted successfully"}), 200
     

#done
@admin_bp.post('/products/add')
@admin_or_vendor_required
def add_products():
    
    try:
        
        data= request.json
        
        product_category= data.get("product_category", "").lower().strip()
        name= data.get("name", "").lower().strip()
        descrption= data.get("description", "").lower().strip()
        price= float(data.get("price").strip())
        stock= int(data.get("stock").strip())
        
        if not product_category or not name or not descrption or not price or not stock:
            return jsonify({"msg":"Please complete the details for the product"}), 400
        
        if Products.query.filter_by(name= name).first():
            return jsonify({"msg":f"Product {name} already exist"}), 403
         
        category= Categories.query.filter_by(name= product_category).first()
        
        if not category:
            return jsonify({"msg": f"There is no category for {product_category}, check your spelling or add the category"}), 404
        
        product= Products(
            category_id= category.id,
            name= name,
            description= descrption,
            price= price,
            stock= stock
        )
        db.session.add(product)
        db.session.commit()
        
        return jsonify({"msg":"Product created successfully"}), 201
    
    except ValueError:
        return jsonify({"msg":"Number required for  stock or price"}), 400
    
    
@admin_bp.get('/products/get')
@admin_required
def get_all_products():
    
    page= request.args.get('page', default= 1, type= int)
    content_per_page= request.args.get('content_per_page', default= 6, type= int)
    
    product= Products.query.paginate(
        page= page,
        per_page= content_per_page
    )
    if not product.items:
        return jsonify({"msg":"Page not fond"}), 404
    
    return jsonify({
        "Products": [
            {
                "id": p.id,
                "name":p.name,
                "price":p.price,
                "stock":p.stock,
                "category_id":p.category_id,
                "description":p.description
            }for p in product.items],
        "Total": product.total
    }), 200
     
        
#done
@admin_bp.put('/products/update/<int:product_id>')
@admin_or_vendor_required
def update_product(product_id):
    
    try:
            
        product= Products.query.get(product_id)
        if not product:
            return jsonify({"msg":f"product with id {product_id} not found"}), 404
        
        
        data= request.json
        
        name= data.get("name", product.name).strip().lower()
        price= float(data.get("price", product.price))
        stock= int(data.get("stock", product.stock))
        descrption= data.get("description", product.description).strip().lower()
        product_category= data.get("product_category")
        
        if not product_category:
            product.category_id= product.category_id
            
        else:  
            product_category= product_category.lower().strip()
        
            category= Categories.query.filter_by(name= product_category).first() 
        
            if not category:
                return jsonify({"msg": f"There is no category for {product_category}, check your spelling or add the category"}), 404
            
            product.category_id= category.id
        
        product.name= name
        product.price= price
        product.stock= stock
        product.description= descrption

        db.session.commit()
        return jsonify({"msg":"Update saved"}), 200
    except ValueError:
        return jsonify({"msg":"Please number required in the price or stock field"}), 400


@admin_bp.delete('/products/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    
    products= Products.query.get(product_id)
    if not products:
        return jsonify({"msg":f"product with id {product_id} not found"}), 404
    
    db.session.delete(products)
    db.session.commit()
    return jsonify({"msg":"Deleted successfully"}), 200


#done
@admin_bp.patch('orders/status/<int:order_id>')
@admin_required
def update_order_status(order_id):
    
    data= request.json
    status= data.get("status", "").lower().strip()
    
    order= Orders.query.get(order_id)
    if order:
        
        if status == 'shipped':
            order.status = status
            order.time_sent= datetime.utcnow()
            
        elif status == 'received':
            order.status= status
            order.time_received= datetime.utcnow()
            
        else:
            return jsonify({"msg":"Invalid status remark"}), 400
    
        db.session.commit()
        return jsonify({"msg":"status updated"}), 200
    
    return jsonify({ "msg": "Order not found"}), 404


@admin_bp.post('/users/role/<int:user_id>')
@admin_required
def update_user_role(user_id):
    
    user= Users.query.get(user_id)
    if not user:
        return jsonify({ "msg": f"User with {id} not found"}), 404
    
    user.role = "vendor"
    db.session.commit()
    return jsonify({"msg":f"User role for '{user.email}' updated"}), 200


@admin_bp.post('/users/suspend/<int:user_id>')
@admin_required
def suspend_user(user_id):
    
    user= Users.query.get(user_id)
    if not user:
        return jsonify({ "msg":"User not found"}), 404
    
    user.status= "suspended"
    db.session.commit()
    return jsonify({"msg":f"Account for '{user.email}' suspended successfully"}), 200


 
     
