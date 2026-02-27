# ''' This is database table setting and relationship defining '''
import re
from extension import db
from datetime import datetime
from flask_login import UserMixin


''' Relationship: one to many '''
class Users(db.Model, UserMixin):
    __tablename__= 'users'
    
    id= db.Column(db.Integer, primary_key= True, autoincrement= True)
    email= db.Column(db.String(60), nullable= False, unique= True)
    password= db.Column(db.String(120), nullable=False)
    email_verified= db.Column(db.Boolean, nullable=False, default= False)
    status= db.Column(db.String(50), nullable=False, default= 'active')
    role= db.Column(db.String(50),nullable= False,  default= 'user')
    created_at= db.Column(db.DateTime, default= datetime.utcnow)
    
    # relationships
    carts= db.relationship('Carts', back_populates='users')
    orders= db.relationship('Orders', back_populates='users')
    profiles= db.relationship('Profiles', back_populates='users')
    payments= db.relationship('Payments', back_populates='users')
    reviews= db.relationship('Reviews', back_populates='users')
    

class TokenBlockList(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    jti= db.Column(db.String(100), nullable= False)
    created_at= db.Column(db.DateTime, default= datetime.utcnow)
    
   
# ''' Relationship: one to one '''
class Profiles(db.Model):
    __tablename__= 'profiles'
    
    id= db.Column(db.Integer, primary_key= True)
    user_id= db.Column(db.Integer, db.ForeignKey('users.id'), unique= True)
    first_name= db.Column(db.String(120), nullable= False)
    last_name= db.Column(db.String(120), nullable= False)
    phone= db.Column(db.String(100), nullable= False, unique= True)
    address= db.Column(db.Text, nullable= False)
    country= db.Column(db.String(100), nullable= False)
    
    # relationships
    users= db.relationship('Users', back_populates= 'profiles', uselist= False)
    
    def number_format(phone):
        phone= phone.strip()
        phone= re.sub(r'\D','', phone)
        
        if phone.startswith('0'):
            phone= "234" + phone[1:]
            
        return "+" + phone

      
class Categories(db.Model):
    __tablename__= 'categories'
    
    id= db.Column(db.Integer, primary_key= True)
    name= db.Column(db.String(120), nullable= False)
    description= db.Column(db.String(120), nullable=False)
    
    # relationships
    products= db.relationship('Products', back_populates='categories')
    

class Products(db.Model):
    __tablename__= 'products'
    
    id= db.Column(db.Integer, primary_key= True, autoincrement= True)
    category_id= db.Column(db.Integer, db.ForeignKey('categories.id'))
    name= db.Column(db.String(120), nullable= False)
    description= db.Column(db.String(120), nullable=False)
    price= db.Column(db.Float, default= 0.00, nullable= False)
    stock= db.Column(db.Integer, default= 0, nullable= False)
    created_at= db.Column(db.DateTime, default= datetime.utcnow)
    
    
    # relationships
    categories= db.relationship('Categories', back_populates='products')
    cart_items= db.relationship('CartItems', back_populates='products')
    order_items= db.relationship('OrderItems', back_populates='products')
    reviews= db.relationship('Reviews', back_populates= 'products')


class Carts(db.Model):
    __tablename__= 'carts'
    
    id= db.Column(db.Integer, primary_key= True, autoincrement= True)
    user_id= db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at= db.Column(db.DateTime, default= datetime.utcnow)
    
    # relationships
    users= db.relationship("Users", back_populates='carts')
    cart_items= db.relationship('CartItems', back_populates='carts', cascade= 'all, delete-orphan')
    
   
class CartItems(db.Model):
    __tablename__= 'cart_items'
    
    id= db.Column(db.Integer, primary_key= True, autoincrement= True)
    cart_id= db.Column(db.Integer, db.ForeignKey('carts.id'))
    product_id= db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name= db.Column(db.String(60), nullable= False)
    price= db.Column(db.Float, nullable= False)
    quantity= db.Column(db.Integer, nullable= False, default= 1)
    
    # relationships
    carts= db.relationship('Carts', back_populates='cart_items')
    products= db.relationship('Products', back_populates='cart_items')
    

class Orders(db.Model):
    __tablename__= 'orders'
    
    id= db.Column(db.Integer, primary_key= True, autoincrement= True)
    user_id= db.Column(db.Integer, db.ForeignKey('users.id'))
    total_amount= db.Column(db.Float, nullable= False)
    status= db.Column(db.String(60), default= 'pending')
    revoked= db.Column(db.Boolean, nullable= False, default= False)
    delivery_address= db.Column(db.Text, nullable= False)
    created_at= db.Column(db.DateTime, default= datetime.utcnow)
    reference= db.Column(db.String(60))
    time_sent= db.Column(db.DateTime)
    time_received= db.Column(db.DateTime)
    
    # relationships
    users= db.relationship('Users', back_populates= 'orders')
    order_items= db.relationship('OrderItems', back_populates='orders')
    payments= db.relationship('Payments', back_populates='orders')
   
   
class OrderItems(db.Model):
    __tablename__= 'order_items'
    
    id= db.Column(db.Integer, primary_key= True, autoincrement= True)
    order_id=  db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id= db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name= db.Column(db.String(60), nullable= False)
    quantity= db.Column(db.Integer, nullable= False)
    price= db.Column(db.Float, default= 0.00, nullable= False)
    revoked= db.Column(db.Boolean, nullable= False, default= False)
    
    # relationships
    orders= db.relationship('Orders', back_populates='order_items')
    products= db.relationship('Products', back_populates='order_items')
    

class Reviews(db.Model):
    __tablename__= 'reviews'
    
    id= db.Column(db.Integer, primary_key= True, autoincrement= True)
    user_id= db.Column(db.Integer, db.ForeignKey('users.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id= db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name= db.Column(db.String(60))
    rating= db.Column(db.Integer)
    comment= db.Column(db.String(500))
    created_at= db.Column(db.DateTime, default= datetime.utcnow)
    
    # relationships
    users= db.relationship('Users', back_populates='reviews')
    products= db.relationship('Products', back_populates='reviews')
    

class Payments(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), default= 'paystack')
    payment_status = db.Column(db.String(50), default='pending')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    #relationships
    orders = db.relationship("Orders", back_populates="payments")
    users = db.relationship("Users", back_populates="payments")




