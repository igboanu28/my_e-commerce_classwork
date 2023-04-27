from app import db, login
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import json
from sqlalchemy.ext import mutable




class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    user_type = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
    
@login.user_loader
def load_user(id):    
    return User.query.get(int(id))



class Products(db.Model):
    __searchable__ = ['name','description']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(65), nullable=False)
    price = db.Column(db.Numeric(10,2), nullable=False)  
    description = db.Column(db.Text, nullable=False)
    discount = db.Column(db.Integer, default=0)
    image_file = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref="products")
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f'<Products {self.name}>'
    
class Category(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)

    def __repr__(self):
        return f'<Category {self.name}>'



class JsonEncodedDict(db.TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = db.Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)


class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    orders = db.Column(JsonEncodedDict)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<CustomerOrder {}>'.format(self.invoice)
