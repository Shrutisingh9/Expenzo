from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "supersecretkey"
bcrypt = Bcrypt(app)

# ===== MongoDB Atlas Setup =====
MONGO_URI = "mongodb+srv://tanukumss784_db_user:grqXrrFhic8IhQzL@cluster0.df53h7a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["expenzo_db"]

users_col = db["users"]
transactions_col = db["transactions"]
cards_col = db["cards"]
subscriptions_col = db["subscriptions"]

# ===== ROUTES =====

@app.route('/')
def index():
    return render_template('index.html')

# ===== LOGIN =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_col.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password!")

    return render_template('login.html')

# ===== REGISTER =====
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        dob = request.form['dob']

        existing_user = users_col.find_one({'email': email})
        if existing_user:
            return render_template('register.html', error="User already exists with this email!")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        users_col.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'phone': phone,
            'dob': dob,
            'created_at': datetime.utcnow()
        })

        return redirect(url_for('login'))

    return render_template('register.html')

# ===== DASHBOARD =====
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    name = session['name']

    # Dummy example: you can insert sample data manually for testing
    transactions = list(transactions_col.find({'user_id': user_id}))
    cards = list(cards_col.find({'user_id': user_id}))
    subscriptions = list(subscriptions_col.find({'user_id': user_id}))

    total_income = sum([float(t.get('amount', 0)) for t in transactions if t.get('type') == 'income'])
    total_expense = sum([float(t.get('amount', 0)) for t in transactions if t.get('type') == 'expense'])

    balance = total_income - total_expense

    return render_template(
        'dashboard.html',
        name=name,
        transactions=transactions,
        cards=cards,
        subscriptions=subscriptions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )

# ===== LOGOUT =====
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ===== FEATURES PAGE =====
@app.route('/features')
def features():
    return render_template('features.html')

# ===== RUN APP =====
if __name__ == "__main__":
    app.run(debug=True)
