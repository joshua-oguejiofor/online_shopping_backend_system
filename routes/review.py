from extension import db
# from logger import logger
from flask import request, jsonify, Blueprint
from flask_jwt_extended import current_user, jwt_required
from models import OrderItems, Reviews



review_bp= Blueprint('reviews', __name__)


@review_bp.post('/reviews')
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

