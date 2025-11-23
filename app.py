from flask import Flask, request, jsonify
from datetime import datetime
from decimal import Decimal
import uuid
import bcrypt
import configparser
import urllib.parse

from pymongo import MongoClient
from flask_cors import CORS

# ---------------------------------------------------------
# Import all Part 1 (FX logic) functions from fx_api.py
# ---------------------------------------------------------
from fx_api import (
    get_country_currency,
    get_current_rate,
    get_currency_conversion_result,
    get_supported_currencies,
    get_monthly_rates,
    analyze_rate_trend,
)

# ---------------------------------------------------------
# Flask App
# ---------------------------------------------------------
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------
# Load MongoDB Config (.properties file)
# ---------------------------------------------------------
def load_db_config():
    config = configparser.RawConfigParser()
    config.read("conf/db.properties")

    prefix = config.get("DEFAULT", "db.prefix")
    username = urllib.parse.quote_plus(config.get("DEFAULT", "db.user"))
    password = urllib.parse.quote_plus(config.get("DEFAULT", "db.pwd"))
    db_url = config.get("DEFAULT", "db.dbUrl")
    db_params = config.get("DEFAULT", "db.params")
    db_name = config.get("DEFAULT", "db.dbName")

    uri = f"{prefix}{username}:{password}{db_url}{db_params}"
    return uri, db_name


# ---------------------------------------------------------
# MongoDB Setup
# ---------------------------------------------------------
import certifi
mongo_uri, db_name = load_db_config()

client = MongoClient(
    mongo_uri,
    tlsCAFile=certifi.where()     # <--- FIX SSL ERROR HERE
)

db = client[db_name]

users = db["users"]
sessions = db["sessions"]
records = db["records"]

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def hash_pw(password: str) -> bytes:
    if (len(password)>64): return
    try :
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    except:
        return 


def check_pw(password: str, hashed: bytes) -> bool:
    if (len(password)>64): return False
    try :
        return bcrypt.checkpw(password.encode(), hashed)
    except:
        return False


def validate_session(session_id: str):
    session = sessions.find_one({"session_id": session_id})
    if not session:
        return None
    return users.find_one({"user_id": session["user_id"]})


# ---------------------------------------------------------
# 1. SIGNUP
# ---------------------------------------------------------
@app.post("/signup")
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if users.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 409

    user_id = str(uuid.uuid4())
    users.insert_one({
        "user_id": user_id,
        "username": username,
        "password": hash_pw(password)
    })

    return jsonify({"user_id": user_id}), 201


# ---------------------------------------------------------
# 2. LOGIN
# ---------------------------------------------------------
@app.post("/login")
def login():
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    user = users.find_one({"username": username})
    if not user or not check_pw(password, user["password"]):
        return jsonify({"error": "Invalid login"}), 401

    session_id = str(uuid.uuid4())
    sessions.insert_one({
        "session_id": session_id,
        "user_id": user["user_id"],
        "created_at": datetime.utcnow(),
    })

    return jsonify({
    "session_id": session_id,
    "user_id": user["username"]
    }), 200

# ---------------------------------------------------------
# 3. LOGOUT
# ---------------------------------------------------------
@app.delete("/login")
def logout():
    session_id = request.json.get("session_id")
    sessions.delete_one({"session_id": session_id})
    return "", 204


# ---------------------------------------------------------
# 4. CONVERT
# ---------------------------------------------------------
@app.post("/convert")
def convert_currency():
    data = request.get_json()

    # Validate session
    session = validate_session(data.get("session_id"))
   
    #return jsonify({"error": "Invalid session"}), 401

    base_country = data.get("base_country_name")
    target_country = data.get("target_country_name")

    amount = Decimal(str(data.get("amount")))

    try:
        #base_currency = get_country_currency(base_country)
        #target_currency = get_country_currency(target_country)
        base_currency = (base_country)
        target_currency = (target_country)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    rate = get_current_rate(base_currency, target_currency)
    result = get_currency_conversion_result(base_currency, target_currency, amount)

    record_id = str(uuid.uuid4())

    if session:
        records.insert_one({
            "record_id": record_id,
            "user_id": session["user_id"],
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "base_currency": base_currency,
            "target_currency": target_currency,
            "amount": float(amount),
            "rate": float(rate),
            "result": float(result)
        })

    return jsonify({
        "record_id": record_id,
        "base_country_name": base_country,
        "base_currency_name": base_currency,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "target_country_name": target_country,
        "target_currency_name": target_currency,
        "amount": float(amount),
        "rate": float(rate),
        "result": float(result)
    }), 200


# ---------------------------------------------------------
# 5. GET RATE
# ---------------------------------------------------------
@app.get("/rate")
def get_rate():
    base = request.args.get("base")
    target = request.args.get("target")

    rate = get_current_rate(base, target)
    return jsonify({
        "rate": float(rate),
        "date": str(datetime.utcnow().date())
    }), 200


# ---------------------------------------------------------
# 6. GET RECORDS
# ---------------------------------------------------------
@app.get("/record")
def view_records():
    session_id = request.args.get("session_id")
    session = validate_session(session_id)
    if not session:
        return jsonify({"error": "Invalid session"}), 401

    user_records = list(records.find(
        {"user_id": session["user_id"]},
        {"_id": 0}
    ))
    return jsonify(user_records), 200


# ---------------------------------------------------------
# 7. DELETE RECORD
# ---------------------------------------------------------
@app.delete("/record")
def delete_record():
    data = request.get_json()
    session = validate_session(data.get("session_id"))
    if not session:
        return jsonify({"error": "Invalid session"}), 401

    record_id = data.get("record_id")
    records.delete_one({
        "record_id": record_id,
        "user_id": session["user_id"]
    })

    return "", 204


# ---------------------------------------------------------
# 8. SUPPORTED CURRENCIES
# ---------------------------------------------------------
@app.get("/supported_currencies")
def supported():
    return jsonify(get_supported_currencies()), 200


# ---------------------------------------------------------
# 9. TRENDS
# ---------------------------------------------------------
@app.get("/trends")
def trend():
    base = request.args.get("base")
    target = request.args.get("target")

    rates = get_monthly_rates(base, target)
    trend_num = analyze_rate_trend(rates)

    mapping = {0: "up", 1: "down", 2: "flat"}
    
    return jsonify({
        "trend": mapping[trend_num],
        "rates": rates
    }), 200

#@app.get("/debug/users")
#def list_users():
#    all_users = list(users.find({}, {"_id": 0, "password": 0}))
#    return jsonify(all_users), 200


# ---------------------------------------------------------
# Run Server
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
