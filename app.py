# app.py
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, abort
)
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from datetime import datetime, date, timedelta
from bson.objectid import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
import os
import traceback

# -------------------- CONFIG --------------------
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY not found in environment variables. Please set it in .env file for security.")
bcrypt = Bcrypt(app)

# -------------------- MONGO SETUP --------------------
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not found in environment (.env)")

client = MongoClient(MONGO_URI)
db = client.get_database(os.getenv("DB_NAME", "expen"))

# collections
users_col = db["users"]
transactions_col = db["transactions"]
cards_col = db["cards"]
subscriptions_col = db["subscriptions"]
limits_col = db["limits"]

# -------------------- HELPERS --------------------
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
        data = request.get_json(silent=True) or request.form
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        if db.users.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 400

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        db.users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_pw,
            "created_at": datetime.utcnow()
        })

        # ✅ Always return JSON if the request is from JS
        if request.is_json:
            return jsonify({"message": "User registered successfully!"}), 201

        # ✅ For form-based submission (HTML)
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    # ✅ If it's a GET (for browser)
    if request.is_json:
        return jsonify({"error": "GET not allowed"}), 405

    return render_template("register.html")

# ✅ LOGIN (works for both frontend + Postman)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        email = data.get("email")
        password = data.get("password")

        user = db.users.find_one({"email": email})
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

    # ✅ Redirect for frontend
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))  # ✅ correct


# -------------------- DASHBOARD (page + API) --------------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        if "user_id" not in session:
            # 🔹 If Postman or JSON request → return JSON instead of redirect
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"error": "Unauthorized. Please log in first."}), 401
            return redirect(url_for("login"))

        user_id = session["user_id"]

        # Query user-specific data with error handling
        try:
            cards = list(cards_col.find({"user_id": user_id}))
            recent_transactions = list(transactions_col.find({"user_id": user_id}).sort("created_at", -1).limit(6))
            subs = list(subscriptions_col.find({"user_id": user_id}).sort("next_payment_date", 1).limit(6))
            user_limit = limits_col.find_one({"user_id": user_id})
        except Exception as e:
            print(f"Database query error in dashboard: {str(e)}")
            print(traceback.format_exc())
            cards = []
            recent_transactions = []
            subs = []
            user_limit = None

        # Compute totals with error handling
        try:
            all_tx = list(transactions_col.find({"user_id": user_id}))
            total_income = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "income")
            total_expense = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "expense")
            balance = total_income - total_expense
            
            # Calculate category spending for expenses
            category_spending = {}
            for t in all_tx:
                if t.get("type") == "expense":
                    category = t.get("category") or "Other"
                    try:
                        amount = float(t.get("amount", 0))
                        category_spending[category] = category_spending.get(category, 0) + amount
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"Error calculating totals in dashboard: {str(e)}")
            print(traceback.format_exc())
            total_income = 0.0
            total_expense = 0.0
            balance = 0.0
            category_spending = {}

        # Convert ObjectIds for JSON with error handling
        try:
            for c in cards:
                if "_id" in c and c["_id"]:
                    c["_id"] = str(c["_id"])
            for t in recent_transactions:
                if "_id" in t and t["_id"]:
                    t["_id"] = str(t["_id"])
            for s in subs:
                if "_id" in s and s["_id"]:
                    s["_id"] = str(s["_id"])
        except Exception as e:
            print(f"Error converting ObjectIds in dashboard: {str(e)}")
            print(traceback.format_exc())

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
        try:
            # Ensure all variables have safe defaults
            try:
                total_income_val = float(total_income) if total_income is not None else 0.0
            except (ValueError, TypeError):
                total_income_val = 0.0
            
            try:
                total_expense_val = float(total_expense) if total_expense is not None else 0.0
            except (ValueError, TypeError):
                total_expense_val = 0.0
            
            try:
                balance_val = float(balance) if balance is not None else 0.0
            except (ValueError, TypeError):
                balance_val = 0.0
            
            template_vars = {
                "cards": cards if cards else [],
                "recent_transactions": recent_transactions if recent_transactions else [],
                "subscriptions": subs if subs else [],
                "user_limit": user_limit,
                "total_income": total_income_val,
                "total_expense": total_expense_val,
                "balance": balance_val,
                "category_spending": category_spending if category_spending else {},
                "user_name": session.get("user_name", "User")
            }
            return render_template("dashboard.html", **template_vars)
        except Exception as template_error:
            print("=" * 50)
            print("TEMPLATE RENDERING ERROR IN DASHBOARD")
            print("=" * 50)
            print(f"Template Error: {str(template_error)}")
            print(traceback.format_exc())
            print("=" * 50)
            # Return a simple error page instead of redirecting
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    h1 {{ color: #e74c3c; }}
                    pre {{ background: #f4f4f4; padding: 20px; text-align: left; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <h1>Dashboard Error</h1>
                <p>An error occurred while rendering the dashboard.</p>
                <p><strong>Error:</strong> {str(template_error)}</p>
                <pre>{traceback.format_exc()}</pre>
                <p><a href="/login">Return to Login</a></p>
            </body>
            </html>
            """, 500
    except Exception as e:
        print("=" * 50)
        print("ERROR IN DASHBOARD ROUTE")
        print("=" * 50)
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        print("=" * 50)
        # Return error page with details
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                h1 {{ color: #e74c3c; }}
                pre {{ background: #f4f4f4; padding: 20px; text-align: left; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>Dashboard Error</h1>
            <p>An error occurred while loading the dashboard.</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <pre>{traceback.format_exc()}</pre>
            <p><a href="/login">Return to Login</a></p>
        </body>
        </html>
        """, 500
# -------------------- CARDS --------------------
@app.route("/cards")
def cards_page():
    """Render the user's saved cards in the dashboard UI."""
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))

        user_id = session["user_id"]

        # Fetch user's cards (newest first) with error handling
        try:
            cards = list(cards_col.find({"user_id": user_id}).sort("created_at", -1))
        except Exception as e:
            print(f"Database error in cards_page: {str(e)}")
            print(traceback.format_exc())
            cards = []

        # Convert ObjectIds to strings for rendering
        try:
            for c in cards:
                if "_id" in c and c["_id"]:
                    c["_id"] = str(c["_id"])
        except Exception as e:
            print(f"Error converting ObjectIds in cards_page: {str(e)}")

        return render_template("cards.html", cards=cards if cards else [])
    except Exception as e:
        print(f"Error in cards_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading cards. Please try again.", "error")
        return redirect(url_for("dashboard"))

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
    try:
        if "user_id" not in session:
            return jsonify({"error": "auth required"}), 403

        user_id = session["user_id"]
        cards = list(cards_col.find({"user_id": user_id}))
        for c in cards:
            if "_id" in c and c["_id"]:
                c["_id"] = str(c["_id"])
            # mask card number for security
            if "number" in c:
                c["masked_number"] = "**** **** **** " + str(c["number"])[-4:]
                del c["number"]

        return jsonify({"success": True, "cards": cards}), 200
    except Exception as e:
        print(f"Error in api_get_cards: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Failed to fetch cards"}), 500

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
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))
        
        user_id = session["user_id"]
        
        # Fetch incomes with error handling
        try:
            incomes = list(transactions_col.find({"user_id": user_id, "type": "income"}).sort("created_at", -1).limit(50))
        except Exception as e:
            print(f"Database error in income_page: {str(e)}")
            print(traceback.format_exc())
            incomes = []
        
        # Convert ObjectIds to strings
        try:
            for i in incomes:
                if "_id" in i and i["_id"]:
                    i["_id"] = str(i["_id"])
        except Exception as e:
            print(f"Error converting ObjectIds in income_page: {str(e)}")
        
        return render_template("income.html", incomes=incomes if incomes else [])
    except Exception as e:
        print(f"Error in income_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading income. Please try again.", "error")
        return redirect(url_for("dashboard"))


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
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))
        
        user_id = session["user_id"]
        
        # Fetch expenses with error handling
        try:
            expenses = list(transactions_col.find({"user_id": user_id, "type": "expense"}).sort("created_at", -1).limit(50))
        except Exception as e:
            print(f"Database error in expense_page: {str(e)}")
            print(traceback.format_exc())
            expenses = []
        
        # Convert ObjectIds to strings
        try:
            for e in expenses:
                if "_id" in e and e["_id"]:
                    e["_id"] = str(e["_id"])
        except Exception as e:
            print(f"Error converting ObjectIds in expense_page: {str(e)}")
        
        return render_template("expense.html", expenses=expenses if expenses else [])
    except Exception as e:
        print(f"Error in expense_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading expenses. Please try again.", "error")
        return redirect(url_for("dashboard"))


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
    try:
        print("=" * 50)
        print("TRANSACTIONS PAGE CALLED")
        print("=" * 50)
        if "user_id" not in session:
            print("No user_id in session, redirecting to login")
            return redirect(url_for("login"))
        
        user_id = session["user_id"]
        print(f"User ID: {user_id}")
        
        # Fetch transactions with error handling
        try:
            txs = list(transactions_col.find({"user_id": user_id})
                       .sort("created_at", -1)
                       .limit(200))
            print(f"Found {len(txs)} transactions")
        except Exception as e:
            print(f"Database error in transactions_page: {str(e)}")
            print(traceback.format_exc())
            txs = []
        
        # Convert ObjectIds to strings
        try:
            for t in txs:
                if "_id" in t and t["_id"]:
                    t["_id"] = str(t["_id"])
        except Exception as e:
            print(f"Error converting ObjectIds in transactions_page: {str(e)}")
        
        print("Rendering transactions.html template...")
        try:
            result = render_template("transactions.html", transactions=txs if txs else [])
            print("Template rendered successfully")
            return result
        except Exception as template_error:
            print("=" * 50)
            print("TEMPLATE RENDERING ERROR IN TRANSACTIONS PAGE")
            print("=" * 50)
            print(f"Template Error: {str(template_error)}")
            print(traceback.format_exc())
            print("=" * 50)
            flash(f"Template error: {str(template_error)}", "error")
            # Don't redirect, show error page instead
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Transactions Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 50px; }}
                    h1 {{ color: #e74c3c; }}
                    pre {{ background: #f4f4f4; padding: 20px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <h1>Transactions Page Error</h1>
                <p><strong>Error:</strong> {str(template_error)}</p>
                <pre>{traceback.format_exc()}</pre>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body>
            </html>
            """, 500
    except Exception as e:
        print(f"Error in transactions_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading transactions. Please try again.", "error")
        return redirect(url_for("dashboard"))


# ✅ Get all transactions (for Postman)
@app.route("/api/transactions", methods=["GET"])
def api_get_all_transactions():
    try:
        if "user_id" not in session:
            return jsonify({"error": "auth required"}), 403
        
        user_id = session["user_id"]
        txs = list(transactions_col.find({"user_id": user_id}).sort("created_at", -1))
        for t in txs:
            if "_id" in t and t["_id"]:
                t["_id"] = str(t["_id"])
        return jsonify({"success": True, "transactions": txs}), 200
    except Exception as e:
        print(f"Error in api_get_all_transactions: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Failed to fetch transactions"}), 500


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
    try:
        print("=" * 50)
        print("LIMITS PAGE CALLED")
        print("=" * 50)
        if "user_id" not in session:
            print("No user_id in session, redirecting to login")
            return redirect(url_for("login"))
        
        user_id = session["user_id"]
        print(f"User ID: {user_id}")
        
        # Fetch limit with error handling
        try:
            limit = limits_col.find_one({"user_id": user_id})
            print(f"Limit found: {limit}")
        except Exception as e:
            print(f"Database error in limits_page: {str(e)}")
            print(traceback.format_exc())
            limit = None
        
        print("Rendering limits.html template...")
        try:
            result = render_template("limits.html", limit=limit)
            print("Template rendered successfully")
            return result
        except Exception as template_error:
            print("=" * 50)
            print("TEMPLATE RENDERING ERROR IN LIMITS PAGE")
            print("=" * 50)
            print(f"Template Error: {str(template_error)}")
            print(traceback.format_exc())
            print("=" * 50)
            flash(f"Template error: {str(template_error)}", "error")
            # Don't redirect, show error page instead
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Limits Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 50px; }}
                    h1 {{ color: #e74c3c; }}
                    pre {{ background: #f4f4f4; padding: 20px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <h1>Limits Page Error</h1>
                <p><strong>Error:</strong> {str(template_error)}</p>
                <pre>{traceback.format_exc()}</pre>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body>
            </html>
            """, 500
    except Exception as e:
        print(f"Error in limits_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading limits. Please try again.", "error")
        return redirect(url_for("dashboard"))


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
        doc["_id"] = str(existing["_id"])
    else:
        res = limits_col.insert_one(doc)
        message = "Limit set successfully"
        doc["_id"] = str(res.inserted_id)
    
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
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))
        
        user_id = session["user_id"]
        
        # Fetch subscriptions with error handling
        try:
            subs = list(subscriptions_col.find({"user_id": user_id}).sort("next_payment_date", 1))
        except Exception as e:
            print(f"Database error in subscriptions_page: {str(e)}")
            print(traceback.format_exc())
            subs = []
        
        # Convert ObjectIds to strings
        try:
            for s in subs:
                if "_id" in s and s["_id"]:
                    s["_id"] = str(s["_id"])
        except Exception as e:
            print(f"Error converting ObjectIds in subscriptions_page: {str(e)}")
        
        return render_template("subscriptions.html", subscriptions=subs if subs else [])
    except Exception as e:
        print(f"Error in subscriptions_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading subscriptions. Please try again.", "error")
        return redirect(url_for("dashboard"))


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
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))
        
        user_id = session["user_id"]
        
        # Get all transactions for visualization with error handling
        try:
            txs = list(transactions_col.find({"user_id": user_id}))
        except Exception as e:
            print(f"Database error in visualization_page: {str(e)}")
            print(traceback.format_exc())
            txs = []
        
        # Calculate totals with error handling
        try:
            total_income = sum(float(t.get("amount", 0)) for t in txs if t.get("type") == "income")
            total_expense = sum(float(t.get("amount", 0)) for t in txs if t.get("type") == "expense")
        except Exception as e:
            print(f"Error calculating totals in visualization_page: {str(e)}")
            total_income = 0.0
            total_expense = 0.0
        
        # Calculate category expenses with error handling
        category_expenses = {}
        income_sources = {}
        
        try:
            for t in txs:
                try:
                    amt = float(t.get("amount", 0))
                    if t.get("type") == "expense":
                        category = t.get("category") or "Other"
                        category_expenses[category] = category_expenses.get(category, 0) + amt
                    elif t.get("type") == "income":
                        source = t.get("source") or "Other"
                        income_sources[source] = income_sources.get(source, 0) + amt
                except (ValueError, TypeError):
                    continue
        except Exception as e:
            print(f"Error calculating categories in visualization_page: {str(e)}")
        
        # Convert ObjectIds for JSON
        try:
            for t in txs:
                if "_id" in t and t["_id"]:
                    t["_id"] = str(t["_id"])
        except Exception as e:
            print(f"Error converting ObjectIds in visualization_page: {str(e)}")
        
        return render_template(
            "visualization.html",
            total_income=total_income,
            total_expense=total_expense,
            category_expenses=category_expenses if category_expenses else {},
            income_sources=income_sources if income_sources else {},
            transactions=txs if txs else []
        )
    except Exception as e:
        print(f"Error in visualization_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading visualization. Please try again.", "error")
        return redirect(url_for("dashboard"))

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
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))
        
        user_id = session["user_id"]
        
        # Get user data with error handling
        try:
            user = users_col.find_one({"_id": ObjectId(user_id)})
        except (InvalidId, ValueError, Exception) as e:
            print(f"Error in profile_page (ObjectId conversion): {str(e)}")
            print(traceback.format_exc())
            flash("Invalid user session. Please log in again.", "error")
            session.clear()
            return redirect(url_for("login"))
        
        if not user:
            flash("User not found", "error")
            session.clear()
            return redirect(url_for("login"))
        
        # Get user statistics with error handling
        try:
            all_tx = list(transactions_col.find({"user_id": user_id}))
            total_income = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "income")
            total_expense = sum(float(t.get("amount", 0)) for t in all_tx if t.get("type") == "expense")
            balance = total_income - total_expense
        except Exception as e:
            print(f"Error calculating statistics in profile_page: {str(e)}")
            print(traceback.format_exc())
            all_tx = []
            total_income = 0.0
            total_expense = 0.0
            balance = 0.0
        
        # Get counts with error handling
        try:
            cards_count = cards_col.count_documents({"user_id": user_id})
            subscriptions_count = subscriptions_col.count_documents({"user_id": user_id})
            transactions_count = len(all_tx)
        except Exception as e:
            print(f"Error getting counts in profile_page: {str(e)}")
            cards_count = 0
            subscriptions_count = 0
            transactions_count = 0
        
        # Convert ObjectId to string for template (if needed)
        try:
            if "_id" in user:
                user["_id"] = str(user["_id"])
        except Exception as e:
            print(f"Error converting user ObjectId in profile_page: {str(e)}")
        
        return render_template(
            "profile.html",
            user=user,
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            cards_count=cards_count,
            subscriptions_count=subscriptions_count,
            transactions_count=transactions_count
        )
    except Exception as e:
        print(f"Error in profile_page: {str(e)}")
        print(traceback.format_exc())
        flash("An error occurred loading profile. Please try again.", "error")
        return redirect(url_for("dashboard"))

# -------------------- ERROR HANDLERS --------------------
@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Errors with detailed logging."""
    error_trace = traceback.format_exc()
    print("=" * 50)
    print("500 INTERNAL SERVER ERROR")
    print("=" * 50)
    print(error_trace)
    print("=" * 50)
    
    # Return a simple error page
    error_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>500 - Internal Server Error</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            h1 {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>500 - Internal Server Error</h1>
        <p>An error occurred while processing your request.</p>
        <p><a href="/dashboard">Return to Dashboard</a></p>
    </body>
    </html>
    """
    return error_html, 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    error_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>404 - Not Found</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #3498db; }
        </style>
    </head>
    <body>
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <p><a href="/dashboard">Return to Dashboard</a></p>
    </body>
    </html>
    """
    return error_html, 404

# -------------------- RUN --------------------
if __name__ == "__main__":
    # For production, set FLASK_DEBUG=False in .env file
    # Default to False for production safety
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
    