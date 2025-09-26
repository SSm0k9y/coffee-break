import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "Fl1nTcR4b4032"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coffee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)

@app.before_request
def init_cart():
    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    products = Product.query.all()
    return render_template('menu.html', products=products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get('cart', {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    cart_data = session.get('cart', {})
    cart_items = []
    total = 0
    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))
        if product:
            cart_items.append({"product": product, "qty": qty})
            total += product.price * qty
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/update_cart/<int:product_id>/<action>')
def update_cart(product_id, action):
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        if action == "increase":
            cart[pid] += 1
        elif action == "decrease":
            cart[pid] -= 1
            if cart[pid] <= 0:
                del cart[pid]
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            new_product = Product(
                name=name,
                price=price,
                image=f'images/{filename}'
            )
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('admin'))

    products = Product.query.all()
    return render_template('admin.html', products=products)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
