from flask import request, jsonify, Blueprint
from flask_jwt_extended import  jwt_required
from models import Categories, Products



product_bp= Blueprint('products', __name__)




@product_bp.get('/products/get')
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

    
@product_bp.get('/products/<int:product_id>')
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
       

@product_bp.get('/products/categories')
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
    
    
@product_bp.post('/products/search')
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

