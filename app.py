from flask import Flask, render_template,request,redirect,url_for,session,jsonify
from flask_sqlalchemy import SQLAlchemy
import base64
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 's3cr3t!K3y@1234#Flask'


db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)

    # One-to-Many Relationship with Item_listed
    items = db.relationship('Item_listed', backref='user', lazy=True, cascade="all, delete")



class Item_listed(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary key for items
    title = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=True)
    features = db.Column(db.String(50), nullable=True)
    defects = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Integer, nullable=False)
    payment_methods = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    shipping = db.Column(db.String(50), nullable=True)
    contact = db.Column(db.String(50), nullable=False)
    return_policy = db.Column(db.String(50), nullable=True)
    warranty = db.Column(db.String(50), nullable=True)
    photo = db.Column(db.LargeBinary, nullable=False)

    # Foreign Key linking Item_listed to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)




with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        shopname = request.form['shopname']
        lat = request.form['lat']
        lng = request.form['lng']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return 'Username or Email already exists!'
        
        new_user = User(email=email, username=username, password=hashed_password,name=shopname,lat=lat,lng=lng)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return 'Invalid credentials!'
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])  # Fetch logged-in user
      # Get all items listed by this user

    return render_template('dashboard.html', user=user)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route("/user")
def user():
    return render_template('user.html')



@app.route("/listing",methods=["GET", "POST"])


@app.route('/listing_Item', methods=['GET', 'POST'])
def listing_Item():
    if 'user_id' not in session:  # Check if user is logged in
        return redirect(url_for('login'))

    user_id = session['user_id']  # Get logged-in user's ID

    if request.method == "POST":
        title = request.form['title']
        category = request.form['category']
        brand = request.form['brand']
        model = request.form.get('model', None)
        features = request.form['features']
        defects = request.form.get('defects', None)  # Fix None default
        price = int(request.form['price'])  # Convert to integer
        payment_methods = request.form['payment_methods']
        quantity = request.form['quantity']
        location = request.form['location']
        shipping = request.form['shipping']
        contact = request.form['contact']
        return_policy = request.form['return_policy']
        warranty = request.form.get('warranty', None)  # Fix None default

        photo = request.files.get('photo')
        if photo:
            photo_binary = photo.read()  # Convert to binary
        else:
            photo_binary = None  # Handle missing photo case

        # Create item entry
        item_listed = Item_listed(
            user_id=user_id, title=title, category=category, brand=brand, 
            model=model, features=features, defects=defects, price=price, 
            payment_methods=payment_methods, quantity=quantity, location=location, 
            shipping=shipping, contact=contact, return_policy=return_policy, 
            warranty=warranty, photo=photo_binary
        )

        db.session.add(item_listed)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('itemlisting.html')  # Render form if GET request


@app.route("/item")
def show():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    

    items = Item_listed.query.filter_by(user_id=session['user_id']).all()   
    
    # Convert binary photo data to base64
    for item in items:
        if item.photo:
            # Encode the photo to base64 string
            item.photo = base64.b64encode(item.photo).decode('utf-8')
    return render_template('showitem.html', items=items)




@app.route("/get_places")
def get_places():
    places = User.query.all()
    return jsonify([{"id": p.id,"name": p.name, "lat": p.lat, "lng": p.lng} for p in places])

@app.route("/shop/<int:shop_id>")
def shop_page(shop_id):
    # Fetch the user (acting as a shop) by ID
    shop = User.query.get(shop_id)  # Use the correct model name

    if not shop:
        return "Shop not found!", 404  # Handle case where shop does not exist

    # Fetch items listed by this user (shop)
    
    shop_items = Item_listed.query.filter_by(user_id=shop.id).all()  # Correct filtering
    for item in shop_items:
        if item.photo:
            # Encode the photo to base64 string
            item.photo = base64.b64encode(item.photo).decode('utf-8')

    return render_template("shop.html", shop=shop, items=shop_items)



@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    # Search for items by title
    items = Item_listed.query.filter(Item_listed.title.ilike(f"%{query}%")).all()

    # Convert image to base64
    results = []
    for item in items:
        photo_base64 = base64.b64encode(item.photo).decode('utf-8') if item.photo else ""

        results.append({
            "id": item.id,
            "title": item.title,
            "price": item.price,
            "shop_id": item.user_id,
            "shop_name": User.query.get(item.user_id).name,
            "photo": photo_base64
        })

    return jsonify(results)
 

if __name__ == "__main__":
    app.run(debug=True)
