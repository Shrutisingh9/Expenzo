# app.py
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, abort
)
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from datetime import datetime, date, timedelta
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import ssl
import certifi

# -------------------- CONFIG --------------------
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "change_this_for_production")
bcrypt = Bcrypt(app)

# -------------------- MONGO SETUP --------------------
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not found in environment (.env)")

# Configure MongoDB client with proper SSL/TLS settings
try:
    # For MongoDB Atlas (mongodb+srv://), SSL is handled automatically
    # For local MongoDB, we don't need SSL
    if MONGO_URI.startswith("mongodb+srv://"):
        # MongoDB Atlas connection - ensure connection string has proper format
        # Add retryWrites and w=majority if not present
        if "retryWrites" not in MONGO_URI:
            separator = "&" if "?" in MONGO_URI else "?"
            MONGO_URI = f"{MONGO_URI}{separator}retryWrites=true&w=majority"
        
        # MongoDB Atlas connection
        # Note: mongodb+srv:// handles TLS automatically
        # Python 3.13 has known SSL issues - certifi upgrade may help
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
    else:
        # Local MongoDB connection
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
    
    # Test the connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
    
except Exception as e:
    error_msg = str(e)
    print(f"❌ MongoDB connection error: {error_msg}")
    print("\n" + "="*60)
    print("TROUBLESHOOTING GUIDE:")
    print("="*60)
    print("\n1. CHECK YOUR CONNECTION STRING:")
    print("   - Should start with: mongodb+srv://")
    print("   - Format: mongodb+srv://username:password@cluster.mongodb.net/database")
    print("   - Make sure password is URL-encoded if it contains special characters")
    print("\n2. MONGODB ATLAS SETUP:")
    print("   - Go to MongoDB Atlas Dashboard")
    print("   - Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)")
    print("   - Database Access → Verify username and password")
    print("\n3. CONNECTION STRING EXAMPLE:")
    print("   MONGO_URI=mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/expenzo?retryWrites=true&w=majority")
    print("\n4. IF STILL FAILING:")
    print("   - Try using local MongoDB: mongodb://localhost:27017/")
    print("   - Check if your firewall/antivirus is blocking the connection")
    print("   - Verify your internet connection")
    print("="*60)
    
    # Don't raise - allow app to start but operations will fail
    # This way user can see the error message and fix it
    print("\n⚠️  App will start but database operations will fail until connection is fixed.\n")
    client = None  # Set to None so we can check later

# Only set up database if connection succeeded
if client:
    db = client.get_database(os.getenv("DB_NAME", "expen"))
    
    # collections
    users_col = db["users"]
    transactions_col = db["transactions"]
    cards_col = db["cards"]
    subscriptions_col = db["subscriptions"]
    limits_col = db["limits"]
else:
    # Create dummy collections to prevent errors
    db = None
    users_col = None
    transactions_col = None
    cards_col = None
    subscriptions_col = None
    limits_col = None

# -------------------- HELPERS --------------------
def check_db_connection():
    """Check if database connection is available."""
    if not client or not db:
        return False
    try:
        client.admin.command('ping')
        return True
    except:
        return False

def json_or_form(req):
    """Return dict from JSON body or form data."""
    if req.is_json:
        return req.get_json()
    # create dict from form (ImmutableMultiDict)
    return {k: req.form.get(k) for k in req.form.keys()}


def require_login_json():
    """Return a JSON error if user not logged in (for API endpoints)."""
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    return None


# -------------------- PAGE ROUTES (renders) --------------------
@app.route("/")
def index():
    # Landing page
    return render_template("index.html")


@app.route("/features")
def features():
    return render_template("features.html")


# -------------------- AUTH --------------------

# ✅ REGISTER (works for both frontend form + Postman)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            data = request.get_json(silent=True) or request.form
            name = data.get("name")
            email = data.get("email")
            password = data.get("password")

            if not name or not email or not password:
                return jsonify({"error": "All fields are required"}), 400

            # Check if user exists
            if users_col.find_one({"email": email}):
                return jsonify({"error": "User already exists"}), 400

            hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
            result = users_col.insert_one({
                "name": name,
                "email": email,
                "password": hashed_pw,
                "created_at": datetime.utcnow()
            })
            
            # Automatically log in the user after registration
            session["user_id"] = str(result.inserted_id)
            session["user_name"] = name

            # ✅ Always return JSON if the request is from JS
            if request.is_json:
                return jsonify({
                    "message": "User registered successfully!",
                    "redirect": "/dashboard"
                }), 201

            # ✅ For form-based submission (HTML)
            flash("Registration successful! Welcome!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            # Handle MongoDB connection errors
            error_msg = str(e)
            if "ServerSelectionTimeoutError" in error_msg or "SSL" in error_msg:
                return jsonify({"error": "Database connection failed. Please check your MongoDB connection settings."}), 503
            return jsonify({"error": f"Registration failed: {error_msg}"}), 500

    # ✅ If it's a GET (for browser)
    if request.is_json:
        return jsonify({"error": "GET not allowed"}), 405

    return render_template("register.html")




# ✅ LOGIN (works for both frontend + Postman)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            data = request.get_json(silent=True) or request.form
            email = data.get("email")
            password = data.get("password")

            user = users_col.find_one({"email": email})
            if user and bcrypt.check_password_hash(user["password"], password):
                session["user_id"] = str(user["_id"])
                session["user_name"] = user.get("name", "")

                if request.is_json:
                    return jsonify({"message": "Login successful!"}), 200

                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))

            # ✅ Handle invalid creds in both JSON and form mode
            if request.is_json:
                return jsonify({"error": "Invalid email or password"}), 401

            flash("Invalid email or password", "error")
            return redirect(url_for("login"))
        except Exception as e:
            # Handle MongoDB connection errors
            error_msg = str(e)
            if "ServerSelectionTimeoutError" in error_msg or "SSL" in error_msg:
                if request.is_json:
                    return jsonify({"error": "Database connection failed. Please check your MongoDB connection settings."}), 503
                flash("Database connection error. Please try again later.", "error")
                return redirect(url_for("login"))
            raise

    if request.is_json:
        return jsonify({"error": "GET not allowed"}), 405

    return render_template("login.html")



# ✅ LOGOUT (clears session)
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()

    # ✅ JSON response for Postman
    if request.is_json or request.method == "POST":
        return jsonify({"message": "Logged out successfully!"}), 200

    # ✅ Redirect for frontend - redirect to index so Get Started button appears
    flash("Logged out successfully!", "info")
    return redirect(url_for("index"))


# -------------------- DASHBOARD (page + API) --------------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "user_id" not in session:
        # 🔹 If Postman or JSON request → return JSON instead of redirect
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"error": "Unauthorized. Please log in first."}), 401
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Query user-specific data
    cards = list(cards_col.find({"user_id": user_id}))
    recent_transactions = list(transactions_col.find({"user_id": user_id}).sort("created_at", -1).limit(6))
    subs = list(subscriptions_col.find({"user_id": user_id}).sort("next_payment_date", 1).limit(6))
    user_limit = limits_col.find_one({"user_id": user_id})
    if user_limit:
        user_limit["_id"] = str(user_limit["_id"])

    # Compute totals and category breakdown
    all_tx = list(transactions_col.find({"user_id": user_id}))
    total_income = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "income")
    total_expense = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "expense")
    balance = total_income - total_expense
    
    # Calculate spending by category
    category_spending = {}
    for t in all_tx:
        if t.get("type") == "expense":
            category = t.get("category", "Other")
            category_spending[category] = category_spending.get(category, 0) + float(t.get("amount", 0))
    
    # Get recent income and expenses separately
    recent_income = list(transactions_col.find({"user_id": user_id, "type": "income"}).sort("created_at", -1).limit(5))
    recent_expenses = list(transactions_col.find({"user_id": user_id, "type": "expense"}).sort("created_at", -1).limit(5))
    
    for i in recent_income:
        i["_id"] = str(i["_id"])
    for e in recent_expenses:
        e["_id"] = str(e["_id"])

    # Convert ObjectIds for JSON
    for c in cards:
        c["_id"] = str(c["_id"])
    for t in recent_transactions:
        t["_id"] = str(t["_id"])
    for s in subs:
        s["_id"] = str(s["_id"])

    # 🔹 If JSON request (Postman)
    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "message": "Dashboard data fetched successfully!",
            "data": {
                "cards": cards,
                "recent_transactions": recent_transactions,
                "subscriptions": subs,
                "limit": user_limit,
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": balance
            }
        }), 200

    # 🔹 Otherwise (Browser) → render HTML
    return render_template(
        "dashboard.html",
        cards=cards,
        recent_transactions=recent_transactions,
        subscriptions=subs,
        limit=user_limit,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        user_name=session.get("user_name", ""),
        category_spending=category_spending,
        recent_income=recent_income,
        recent_expenses=recent_expenses,
        active_page="dashboard"
    )
# -------------------- CARDS --------------------
@app.route("/cards")
def cards_page():
    """Render the user's saved cards in the dashboard UI."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch user's cards (newest first)
    cards = list(cards_col.find({"user_id": user_id}).sort("created_at", -1))

    # Convert ObjectIds to strings for rendering
    for c in cards:
        c["_id"] = str(c["_id"])

    return render_template("cards.html", cards=cards, active_page="cards")

@app.route("/api/cards", methods=["POST"])
def api_create_card():
    """Create a new payment card for the logged-in user."""
    if "user_id" not in session:
        return jsonify({"error": "Authentication required"}), 403

    data = json_or_form(request)

    # Validate input fields
    required_fields = ["cardholder", "number", "exp_month", "exp_year", "brand"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Validate expiration details
    try:
        exp_month = int(data.get("exp_month"))
        exp_year = int(data.get("exp_year"))
        if exp_month < 1 or exp_month > 12:
            return jsonify({"error": "Invalid expiration month"}), 400
        if exp_year < datetime.utcnow().year:
            return jsonify({"error": "Expiration year must be current or future"}), 400
    except ValueError:
        return jsonify({"error": "Expiration month and year must be numbers"}), 400

    # Mask card number (store last 4 digits only)
    number = data.get("number")
    last4 = number[-4:] if len(number) >= 4 else number
    masked_number = f"**** **** **** {last4}"

    # Prevent duplicates
    existing = cards_col.find_one({
        "user_id": session["user_id"],
        "last4": last4,
        "brand": data.get("brand")
    })
    if existing:
        return jsonify({"error": "This card already exists"}), 409

    # Create and insert card document
    card = {
        "user_id": session["user_id"],
        "cardholder": data.get("cardholder"),
        "last4": last4,
        "masked_number": masked_number,
        "exp_month": exp_month,
        "exp_year": exp_year,
        "brand": data.get("brand"),
        "created_at": datetime.utcnow()
    }

    res = cards_col.insert_one(card)
    card["_id"] = str(res.inserted_id)

    return jsonify({
        "success": True,
        "message": "Card added successfully",
        "card": card
    }), 201
    
# ✅ GET - View all cards
@app.route("/api/cards", methods=["GET"])
def api_get_cards():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403

    user_id = session["user_id"]
    cards = list(cards_col.find({"user_id": user_id}))
    for c in cards:
        c["_id"] = str(c["_id"])
        # mask card number for security
        if "number" in c:
            c["masked_number"] = "**** **** **** " + str(c["number"])[-4:]
            del c["number"]

    return jsonify({"success": True, "cards": cards}), 200

# ✅ DELETE - Remove a card
@app.route("/api/cards/<card_id>", methods=["DELETE"])
def api_delete_card(card_id):
    """Delete a user's saved card."""
    if "user_id" not in session:
        return jsonify({"error": "Authentication required"}), 403

    try:
        obj_id = ObjectId(card_id)
    except Exception:
        return jsonify({"error": "Invalid card ID"}), 400

    result = cards_col.delete_one({
        "_id": obj_id,
        "user_id": session["user_id"]
    })

    if result.deleted_count == 0:
        return jsonify({"error": "Card not found or unauthorized"}), 404

    return jsonify({"success": True, "message": "Card deleted successfully"}), 200

# -------------------- INCOME --------------------
@app.route("/income")
def income_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    incomes = list(transactions_col.find({"user_id": user_id, "type": "income"}).sort("created_at", -1).limit(200))
    for i in incomes:
        i["_id"] = str(i["_id"])
    
    # Calculate total income
    all_income = list(transactions_col.find({"user_id": user_id, "type": "income"}))
    total_income = sum(float(t.get("amount", 0)) for t in all_income)
    
    return render_template("income.html", incomes=incomes, total_income=total_income, active_page="income")


@app.route("/api/income", methods=["POST"])
def api_create_income():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    data = json_or_form(request)
    try:
        amt = float(data.get("amount", 0))
    except Exception:
        return jsonify({"error": "invalid amount"}), 400
    tx = {
        "user_id": session["user_id"],
        "type": "income",
        "amount": amt,
        "source": data.get("source"),
        "date": data.get("date") or datetime.utcnow().isoformat(),
        "note": data.get("note", ""),
        "created_at": datetime.utcnow()
    }
    res = transactions_col.insert_one(tx)
    tx["_id"] = str(res.inserted_id)
    return jsonify({"success": True, "transaction": tx}), 201

@app.route("/api/income", methods=["GET"])
def api_get_income():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    incomes = list(transactions_col.find(
        {"user_id": session["user_id"], "type": "income"}
    ).sort("created_at", -1))
    for i in incomes:
        i["_id"] = str(i["_id"])
    return jsonify(incomes), 200

@app.route("/api/income/<income_id>", methods=["DELETE"])
def api_delete_income(income_id):
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    try:
        obj_id = ObjectId(income_id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400
    
    result = transactions_col.delete_one({
        "_id": obj_id,
        "user_id": session["user_id"],
        "type": "income"
    })
    
    if result.deleted_count == 0:
        return jsonify({"error": "not found or unauthorized"}), 404
    
    return jsonify({"success": True, "message": "Income deleted successfully"}), 200


# -------------------- EXPENSE --------------------
@app.route("/expense")
def expense_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    expenses = list(transactions_col.find({"user_id": user_id, "type": "expense"}).sort("created_at", -1).limit(200))
    for e in expenses:
        e["_id"] = str(e["_id"])
    
    # Calculate total expense
    all_expenses = list(transactions_col.find({"user_id": user_id, "type": "expense"}))
    total_expense = sum(float(t.get("amount", 0)) for t in all_expenses)
    
    return render_template("expense.html", expenses=expenses, total_expense=total_expense, active_page="expense")


@app.route("/api/expense", methods=["POST"])
def api_create_expense():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    data = json_or_form(request)
    try:
        amt = float(data.get("amount", 0))
    except Exception:
        return jsonify({"error": "invalid amount"}), 400
    tx = {
        "user_id": session["user_id"],
        "type": "expense",
        "amount": amt,
        "category": data.get("category"),
        "payee": data.get("payee", ""),
        "date": data.get("date") or datetime.utcnow().isoformat(),
        "note": data.get("note", ""),
        "created_at": datetime.utcnow()
    }
    res = transactions_col.insert_one(tx)
    tx["_id"] = str(res.inserted_id)
    return jsonify({"success": True, "transaction": tx}), 201

@app.route("/api/expense", methods=["GET"])
def api_get_expenses():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    
    expenses = list(transactions_col.find({
        "user_id": session["user_id"],
        "type": "expense"
    }).sort("created_at", -1))
    
    for e in expenses:
        e["_id"] = str(e["_id"])
    
    return jsonify({"success": True, "expenses": expenses}), 200

@app.route("/api/expense/<expense_id>", methods=["DELETE"])
def api_delete_expense(expense_id):
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    try:
        obj_id = ObjectId(expense_id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400
    
    result = transactions_col.delete_one({
        "_id": obj_id,
        "user_id": session["user_id"],
        "type": "expense"
    })
    
    if result.deleted_count == 0:
        return jsonify({"error": "not found or unauthorized"}), 404
    
    return jsonify({"success": True, "message": "Expense deleted successfully"}), 200


# -------------------- TRANSACTIONS --------------------
@app.route("/transactions")
def transactions_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    txs = list(transactions_col.find({"user_id": user_id})
               .sort("created_at", -1)
               .limit(200))
    
    # Calculate totals
    all_txs = list(transactions_col.find({"user_id": user_id}))
    total_income = sum(float(t.get("amount", 0)) for t in all_txs if t.get("type") == "income")
    total_expense = sum(float(t.get("amount", 0)) for t in all_txs if t.get("type") == "expense")
    net_balance = total_income - total_expense
    
    for t in txs:
        t["_id"] = str(t["_id"])
    
    return render_template(
        "transactions.html", 
        transactions=txs, 
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
        active_page="transactions"
    )


# ✅ Get all transactions (for Postman)
@app.route("/api/transactions", methods=["GET"])
def api_get_all_transactions():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    
    txs = list(transactions_col.find({"user_id": session["user_id"]}).sort("created_at", -1))
    for t in txs:
        t["_id"] = str(t["_id"])
    return jsonify({"success": True, "transactions": txs}), 200


# ✅ Get or Delete specific transaction
@app.route("/api/transactions/<tx_id>", methods=["GET", "DELETE"])
def api_transaction_detail(tx_id):
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    try:
        obj_id = ObjectId(tx_id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400

    if request.method == "GET":
        tx = transactions_col.find_one({"_id": obj_id, "user_id": session["user_id"]})
        if not tx:
            return jsonify({"error": "not found"}), 404
        tx["_id"] = str(tx["_id"])
        return jsonify({"success": True, "transaction": tx}), 200

    # DELETE
    result = transactions_col.delete_one({"_id": obj_id, "user_id": session["user_id"]})
    if result.deleted_count == 0:
        return jsonify({"error": "not found or unauthorized"}), 404
    
    return jsonify({"success": True, "message": "Transaction deleted successfully"}), 200


# -------------------- LIMITS --------------------
@app.route("/limits")
def limits_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    limit = limits_col.find_one({"user_id": session["user_id"]})
    if limit:
        limit["_id"] = str(limit["_id"])
    
    return render_template("limits.html", limit=limit, active_page="limits")


# ✅ Get current user's limit
@app.route("/api/limits", methods=["GET"])
def api_get_limit():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403

    limit = limits_col.find_one({"user_id": session["user_id"]})
    if not limit:
        return jsonify({"message": "No limit set yet"}), 200

    limit["_id"] = str(limit["_id"])
    return jsonify({"success": True, "limit": limit}), 200


# ✅ Create or Update Limit
@app.route("/api/limits", methods=["POST", "PUT"])
def api_set_limit():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    
    data = json_or_form(request)
    try:
        limit_amount = float(data.get("limit", 0))
    except Exception:
        return jsonify({"error": "invalid limit"}), 400

    doc = {
        "user_id": session["user_id"],
        "limit": limit_amount,
        "period": data.get("period", "monthly"),
        "updated_at": datetime.utcnow()
    }

    existing = limits_col.find_one({"user_id": session["user_id"]})
    if existing:
        limits_col.update_one({"user_id": session["user_id"]}, {"$set": doc})
        message = "Limit updated successfully"
    else:
        limits_col.insert_one(doc)
        message = "Limit set successfully"

    doc["_id"] = str(existing["_id"]) if existing else str(limits_col.find_one({"user_id": session["user_id"]})["_id"])
    return jsonify({"success": True, "message": message, "limit": doc}), 200

# ✅ DELETE: Remove user's limit
@app.route("/api/limits", methods=["DELETE"])
def api_delete_limit():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    
    result = limits_col.delete_one({"user_id": session["user_id"]})
    
    if result.deleted_count == 0:
        return jsonify({"message": "No limit found to delete"}), 404
    
    return jsonify({"success": True, "message": "Limit deleted successfully"}), 200


# -------------------- SUBSCRIPTIONS --------------------
@app.route("/subscriptions")
def subscriptions_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    subs = list(subscriptions_col.find({"user_id": user_id}).sort("next_payment_date", 1))
    for s in subs:
        s["_id"] = str(s["_id"])
    return render_template("subscriptions.html", subscriptions=subs, active_page="subscriptions")


# ---------- CREATE SUBSCRIPTION ----------
@app.route("/api/subscriptions", methods=["POST"])
def api_create_subscription():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    
    data = json_or_form(request)
    try:
        amount = float(data.get("amount", 0))
    except Exception:
        return jsonify({"error": "invalid amount"}), 400

    next_payment_date = data.get("next_payment_date") or data.get("end_date")

    sub = {
        "user_id": session["user_id"],
        "name": data.get("name"),
        "amount": amount,
        "cycle": data.get("cycle", "monthly"),
        "start_date": data.get("start_date") or datetime.utcnow().isoformat(),
        "end_date": data.get("end_date"),
        "next_payment_date": next_payment_date,
        "notes": data.get("notes", ""),
        "created_at": datetime.utcnow()
    }

    res = subscriptions_col.insert_one(sub)
    sub["_id"] = str(res.inserted_id)

    return jsonify({
        "success": True,
        "message": "Subscription added successfully",
        "subscription": sub
    }), 201


# ---------- VIEW ALL SUBSCRIPTIONS ----------
@app.route("/api/subscriptions", methods=["GET"])
def api_get_subscriptions():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403

    subs = list(subscriptions_col.find({"user_id": session["user_id"]}).sort("next_payment_date", 1))
    for s in subs:
        s["_id"] = str(s["_id"])
    return jsonify({
        "success": True,
        "message": "Subscriptions fetched successfully",
        "subscriptions": subs
    }), 200

# ---------- UPDATE SUBSCRIPTION ----------
@app.route("/api/subscriptions/<sub_id>", methods=["PUT"])
def api_update_subscription(sub_id):
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403
    
    try:
        obj_id = ObjectId(sub_id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400

    data = json_or_form(request)
    update_fields = {}

    for field in ["name", "amount", "cycle", "start_date", "end_date", "next_payment_date", "notes"]:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return jsonify({"error": "no valid fields to update"}), 400

    update_fields["updated_at"] = datetime.utcnow()
    result = subscriptions_col.update_one(
        {"_id": obj_id, "user_id": session["user_id"]},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return jsonify({"error": "subscription not found"}), 404

    updated_sub = subscriptions_col.find_one({"_id": obj_id})
    updated_sub["_id"] = str(updated_sub["_id"])

    return jsonify({
        "success": True,
        "message": "Subscription updated successfully",
        "subscription": updated_sub
    }), 200

# ---------- DELETE SUBSCRIPTION ----------
@app.route("/api/subscriptions/<sub_id>", methods=["DELETE"])
def api_delete_subscription(sub_id):
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403

    try:
        obj_id = ObjectId(sub_id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400

    result = subscriptions_col.delete_one({"_id": obj_id, "user_id": session["user_id"]})

    if result.deleted_count == 0:
        return jsonify({"error": "not found"}), 404

    return jsonify({"success": True, "message": "Subscription deleted successfully"}), 200



# -------------------- UPCOMING SUBSCRIPTIONS (reminders) --------------------
@app.route("/api/subscriptions/upcoming", methods=["GET"])
def api_upcoming_subscriptions():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403

    try:
        days = int(request.args.get("days", 3))  # Default: next 3 days
        if days <= 0:
            days = 3
    except ValueError:
        days = 3

    today = date.today()
    upper = today + timedelta(days=days)
    upcoming = []

    # Fetch user's subscriptions
    subs = subscriptions_col.find({"user_id": session["user_id"]})

    for s in subs:
        npd = s.get("next_payment_date")
        if not npd:
            continue

        # Parse next payment date from various formats
        d = None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                d = datetime.strptime(npd, fmt).date()
                break
            except Exception:
                continue

        # If still not parsed, try ISO format
        if not d:
            try:
                d = datetime.fromisoformat(npd).date()
            except Exception:
                d = None

        # If valid and within reminder window
        if d and today <= d <= upper:
            s["_id"] = str(s["_id"])
            s["days_left"] = (d - today).days
            upcoming.append(s)

    upcoming.sort(key=lambda x: x["next_payment_date"])

    return jsonify({
        "success": True,
        "message": f"Upcoming subscriptions within {days} days",
        "count": len(upcoming),
        "upcoming": upcoming
    }), 200



# -------------------- VISUALIZATION --------------------
@app.route("/visualization")
def visualization_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    txs = list(transactions_col.find({"user_id": user_id}))
    
    # Calculate summary data
    total_income = sum(float(t.get("amount", 0)) for t in txs if t.get("type") == "income")
    total_expense = sum(float(t.get("amount", 0)) for t in txs if t.get("type") == "expense")
    
    # Category breakdown
    category_expenses = {}
    for t in txs:
        if t.get("type") == "expense":
            category = t.get("category", "Other")
            category_expenses[category] = category_expenses.get(category, 0) + float(t.get("amount", 0))
    
    # Income sources
    income_sources = {}
    for t in txs:
        if t.get("type") == "income":
            source = t.get("source", "Other")
            income_sources[source] = income_sources.get(source, 0) + float(t.get("amount", 0))
    
    # Convert ObjectIds in transactions for JSON serialization
    for tx in txs:
        tx["_id"] = str(tx["_id"])
    
    return render_template(
        "visualization.html",
        total_income=total_income,
        total_expense=total_expense,
        category_expenses=category_expenses,
        income_sources=income_sources,
        transactions=txs,
        active_page="visualization"
    )

@app.route("/api/visualization/summary", methods=["GET"])
def api_visualization_summary():
    if "user_id" not in session:
        return jsonify({"error": "auth required"}), 403

    user_id = session["user_id"]
    txs = list(transactions_col.find({"user_id": user_id}))

    summary = {
        "by_type": {"income": 0.0, "expense": 0.0},
        "by_category": {},
        "net_balance": 0.0
    }

    for t in txs:
        try:
            t_type = t.get("type", "").lower()
            amt = float(t.get("amount", 0))
            category = t.get("category") or t.get("source") or "Other"

            # Update type totals
            if t_type in ["income", "expense"]:
                summary["by_type"][t_type] += amt

            # Update category totals
            if category not in summary["by_category"]:
                summary["by_category"][category] = 0
            summary["by_category"][category] += amt

        except Exception as e:
            print("Error processing transaction:", e)
            continue

    # Calculate net balance
    summary["net_balance"] = summary["by_type"]["income"] - summary["by_type"]["expense"]

    return jsonify({
        "success": True,
        "message": "Visualization data fetched successfully!",
        "summary": summary
    }), 200


# -------------------- PROFILE --------------------
@app.route("/profile")
def profile_page():
    """Render the user's profile page."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    
    # Fetch user data from database
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        session.clear()
        return redirect(url_for("login"))
    
    # Calculate user statistics
    all_tx = list(transactions_col.find({"user_id": user_id}))
    total_income = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "income")
    total_expense = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "expense")
    balance = total_income - total_expense
    
    # Count other stats
    cards_count = cards_col.count_documents({"user_id": user_id})
    subscriptions_count = subscriptions_col.count_documents({"user_id": user_id})
    transactions_count = len(all_tx)
    
    # Format user data
    user_data = {
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "created_at": user.get("created_at", datetime.utcnow())
    }
    
    return render_template(
        "profile.html",
        user=user_data,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        cards_count=cards_count,
        subscriptions_count=subscriptions_count,
        transactions_count=transactions_count,
        active_page="profile"
    )


# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
    