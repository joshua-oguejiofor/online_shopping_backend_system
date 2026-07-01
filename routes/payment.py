import os
import hashlib
import hmac
import requests
from extension import db
from flask import request, jsonify, Blueprint
from flask_jwt_extended import current_user, jwt_required
from models import Orders


payment_bp= Blueprint('payments', __name__)


PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")



"""Paystack payment flow"""

"""
user initialize a Paystack payment transaction.
 Backend send payment details (email, amount, reference) to Paystack.
Return the Paystack authorization URL for the frontend to redirect the user.
"""

@payment_bp.post("/initialize_payment/<int:order_id>")
@jwt_required()
def initialize_payment(order_id):
    
    order= Orders.query.filter_by(id= order_id, user_id= current_user.id).first()
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
        "amount": str(amount  * 100), # amount in kobo as paystack uses kobo for transactions and accept it as a string
        "reference": order.reference
    }
    res = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    return jsonify(res.json())

"""
Verify a payment transaction with Paystack.
Receive the payment reference from the frontend, query Paystack's Verify Transaction API and return the transaction details and payment status.
"""
@payment_bp.get("/verify_payment")
def verify_payment():
    reference = request.args.get("reference")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    return jsonify(res.json())



"""eceive the webhook request from Paystack, verify signature, and returns response """
@payment_bp.post('/payments/webhook')
def paystack_webhook():
    payload= request.get_data()
    signature= request.headers.get("x-paystack-signature")
    
    computed_signature= hmac.new(
        PAYSTACK_SECRET.encode(),
        payload,
        hashlib.sha512        
    ).hexdigest()
    
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
