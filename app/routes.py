import secrets
from app import app, db, search
from flask import render_template, flash, redirect, url_for,request,session,make_response
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user,login_required
from werkzeug.urls import url_parse
from app.forms import LoginForm, PasswordForm, RegistrationForm, ProductForm
from app.models import User,Products,Category,CustomerOrder
from datetime import datetime
import os
from flask import send_from_directory
from werkzeug.utils import secure_filename

def category():
    category = Category.query.join(Products, (Category.id == Products.category_id)).all()
    return category


@app.get('/')
def home():
    products = Products.query.all()

    return render_template('home.html', products=products, category=category())

@app.get('/search_result')
def search_result():
    searchword = request.args.get('q')
    products = Products.query.msearch(searchword, fields=['name', 'description'] , limit=3)
    return render_template('result.html', products=products, category=category())

@app.get('/category/<int:id>')
def get_category(id):
    get_products = Products.query.filter_by(category_id=id)
    return render_template('home.html', get_products=get_products, category=category())

@app.get('/details/<int:id>')
def product_details(id):
    products = Products.query.get_or_404(id)
    return render_template('details.html', products=products, category=category())


def MagerDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))
    return False

@app.route('/add_cart', methods=['POST'])
def add_cart():
    try:
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        products = Products.query.filter_by(id=product_id).first()
        if request.method == "POST":
            Items = {product_id:{'name': products.name, 'price': products.price, 'discount': products.discount, 
                                 'quantity': quantity, 'image': products.image_file}}
            if 'Shopcart' in session:
                print(session['Shopcart'])
                if product_id in session['Shopcart']:
                    for key, item in session['Shopcart'].items():
                        if int(key) == int(product_id):
                            session.modified = True
                            item['quantity'] += 1
                    
                else:
                    session['Shopcart'] = MagerDicts(session['Shopcart'], Items)
                    
                    return redirect(request.referrer)
            else:
                session['Shopcart'] = Items
                return redirect(request.referrer)
    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)

@app.get('/view_carts')
def view_carts():
    if 'Shopcart' not in session or len(session['Shopcart']) <= 0:
        return redirect(url_for('home'))
    subtotal = 0 
    grandtotal = 0
    for key, product in session['Shopcart'].items():
        discount = (product['discount']/100) * float(product['price'])
        subtotal += float(product['price']) * int(product['quantity'])
        subtotal -= discount
        grandtotal = float(subtotal)
    return render_template('carts.html', grandtotal=grandtotal, category=category())

@app.route('/editcart/<int:code>', methods=['POST'])
def edit_cart(code):
    if 'Shopcart' not in session or len(session['Shopcart']) <= 0:
        return redirect(url_for('home'))
    if request.method == "POST":
        quantity = request.form.get('quantity')
        try:
            session.modified = True
            for key , item in session['Shopcart'].items():
                if int(key) == code:
                    item['quantity'] = quantity
                    flash('Item Edited')
                    return redirect(url_for('view_carts'))
        except Exception as e:
            print(e)
            return redirect(url_for('view_carts'))

@app.get('/delete_cart/<int:id>')
def delete_cart(id):
    if 'Shopcart' not in session or len(session['Shopcart']) <= 0:
        return redirect(url_for('home'))
    try:
        session.modified = True
        for key , item in session['Shopcart'].items():
            if int(key) == id:
                session['Shopcart'].pop(key, None)
        return redirect(url_for('view_carts'))
        
    except Exception as e:
        print(e)
        return redirect(url_for('view_carts'))

@app.get('/clear_cart')
def clear_cart():
    try:
        session.pop('Shopcart', None)
        return redirect(url_for('home'))
    except Exception as e:
        print(e)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        next_page = request.args.get('next')
        login_user(user)
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.get('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.user_type =request.form.get('user_type')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    form = PasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user: User = User.query.get(current_user.id)
            user.set_password(form.password.data)
            db.session.commit()
            flash ('Password has been updated!')
        
    return render_template('change_password.html', form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.get('/getorder')
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        try:
            order = CustomerOrder(invoice=invoice, customer_id=customer_id,  orders = session['Shopcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shopcart')
           
            flash('Your order has been sent to the admin')
            return redirect(url_for('home'))
        except Exception as e:
            print(e)
            flash('Something went wrong while getting order')
            return redirect(url_for('view_carts'))

@app.route('/orders')
def orders():
    
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = User.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id).first()
        
        for _key, product in orders.orders.items():
            discount = (product['discount']/100) * float(product['price'])
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount

            grandTotal = float(subTotal)

    else:
        return redirect(url_for('login'))
    
    return render_template('order.html', subTotal=subTotal,grandTotal=grandTotal,
                           customer=customer,orders=orders)

@app.route('/delete_orders/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_orders(id):
    orders = CustomerOrder.query.get(id)
    db.session.delete(orders)
    db.session.commit()
    flash (f'The order was deleted from your database')
    return redirect(url_for('orders'))

@app.get('/admin_dashboard/<username>')
@login_required
def admin_dashboard(username):
    categories = Category.query.all()
    view = Products.query.all()
    user = User.query.filter_by(username=username).first_or_404()
    if user.user_type == 'Admin':
        return render_template('admin_dashboard.html', user=user, view=view,categories=categories, category=category())
    else:
        flash('Sorry only Admins')
        return redirect(url_for('home'))

@app.get('/user_dashboard/<username>')
@login_required
def user_dashboard(username):
    categories = Category.query.all()
    view = Products.query.all()
    user = User.query.filter_by(username=username).first_or_404()
    if user.user_type == 'User':
        return render_template('user_dashboard.html', user=user, view=view,categories=categories, category=category())
    else:
        flash('Sorry only Admins')
        return redirect(url_for('home'))

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method=='POST':
        getcat = request.form.get('category')
        cat = Category(name=getcat)
        db.session.add(cat)
        flash(f'The Category {getcat} is added to the database sucessful')
        db.session.commit()
        return redirect(url_for('add_category'))
    return render_template('add_category.html')

@app.get('/view_categories')
@login_required
def view_category():
    category = Category.query.all()

    return render_template('view_category.html', category=category)

@app.route('/edit_categories/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    edit = Category.query.get(id)
    category = request.form.get('category')
    if request.method=='POST':
        edit.name = category
        flash ('Your category has been updtaed')
        db.session.commit()
        return redirect(url_for('view_category'))
    return render_template('edit_category.html', edit=edit)

@app.route('/delete_category/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_category(id):
    category = Category.query.get(id)
    if request.method=='POST':
        db.session.delete(category)
        db.session.commit()
        flash (f'The category {category.name} was deleted from your database')
        return redirect(url_for('view_category'))
    flash (f'The category {category.name} can"t be deleted from your database')
    return redirect(url_for('view_category'))

    


@app.route('/edit_products/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_products(id):
    categories = Category.query.all()
    product = Products.query.get(id)
    form = ProductForm(request.form)
    category=request.form.get('category')
    if request.method=='POST':
        product.name = form.name.data
        product.price = form.price.data
        product.category_id = category
        product.description = form.description.data
        product.discount = form.discount.data
     
        file = request.files['file']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image_file))
            product.image_file = filename
        db.session.commit()
        flash ('Your product has been updated')
        return redirect(url_for('user_dashboard', username=current_user.username))
        

    form.name.data = product.name
    form.price.data = product.price
    form.description.data = product.description
    form.discount.data = product.discount
    return render_template('edit_product.html', form=form,categories=categories,product=product)

@app.post('/delete_product/<int:id>')
def delete_product(id):
    product = Products.query.get(id)
    if request.method =="POST":
        db.session.delete(product)
        db.session.commit()
        flash(f'The product {product.name} was deleted from your database')
        return redirect(url_for('user_dashboard', username=current_user.username))
    flash(f'Sorry you can"t delete product')
    return redirect(url_for('user_dashboard', username=current_user.username))




UPLOAD_FOLDER = "/home/paul/Desktop/my portfolio/app/static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    categories = Category.query.all()
    form = ProductForm()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash ('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            name = request.form.get("name")
            category = request.form.get("category")
            description = request.form.get("description")
            price = request.form.get("price")
            discount = request.form.get('discount')

            new_product=Products(image_file=file.filename,category_id=category, name=name, description=description, price=price, discount=discount)
        
            db.session.add(new_product)
            db.session.commit()
            flash (f'The Product {name} has been added to the database')
    return render_template('add_product.html', form=form,categories=categories)


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)
app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)