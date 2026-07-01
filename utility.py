from flask import jsonify
from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request


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
   
   
   
   
   