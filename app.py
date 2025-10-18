from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "supersecretkey"
bcrypt = Bcrypt(app)

# ===== MongoDB Setup =====
client = MongoClient("mongodb://localhost:27017/")
db = client["expenzo_db"]

users_col = db["users"]
transactions_col = db["transactions"]
cards_col = db["cards"]
subscriptions_col = db["subscriptions"]

# ===== ROUTES =====

@app.route('/')
def index():
    return render_template('index.html')

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
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        dob = request.form['dob']

        # Check if user already exists
        existing_user = users_col.find_one({'email': email})
        if existing_user:
            return "User already exists with this email!"

        # Insert into database
        users_col.insert_one({
            'name': name,
            'email': email,
            'password': password,   # ⚠️ later you should hash this with bcrypt
            'phone': phone,
            'dob': dob
        })

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    name = session['name']

    cards = list(cards_col.find({'user_id': user_id}))
    transactions = list(transactions_col.find({'user_id': user_id}))
    subscriptions = list(subscriptions_col.find({'user_id': user_id}))

    total_income = sum([float(t['amount']) for t in transactions if t['type'] == 'income'])
    total_expense = sum([float(t['amount']) for t in transactions if t['type'] == 'expense'])

    return render_template('dashboard.html',
                           name=name,
                           cards=cards,
                           transactions=transactions,
                           subscriptions=subscriptions,
                           total_income=total_income,
                           total_expense=total_expense)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/features')
def features():
    return render_template('features.html')

if __name__ == "__main__":
    app.run(debug=True)
