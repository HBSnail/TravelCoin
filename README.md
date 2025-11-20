# 🌐 CloudProject – Currency Conversion API

A Flask-based backend using MongoDB, session authentication, and live currency conversion with persistence of conversion history.

---

## 🚀 Features

### 🔐 Authentication

* **Signup** (`POST /signup`)
* **Login** (`POST /login`)
* Returns a **session_id**
* Sessions expire automatically after 24 hours

### 💱 Currency Conversion

* Convert between any two countries
* Uses **Frankfurter API** for FX rates
* Conversion saved to MongoDB under the user’s account

### 📄 Conversion History

* Retrieve all past conversions of the logged-in user
* Uses session_id to identify the user

### 📦 Database (MongoDB Atlas)

Collections created automatically:

* `users`
* `sessions`
* `records`

---

## 📁 Project Structure

```
CloudProject/
│── app.py
│── fx_api.py
│── db.properties
│── README.md
│── requirements.txt
```

---

## ⚙️ Installation

### 1️⃣ Create Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Install SSL Certificates (MacOS ONLY)

```bash
/Applications/Python\ 3.12/Install\ Certificates.command
```

---

## 🔧 Configuration (`db.properties`)

Example **db.properties**:

```
[DB]
prefix = mongodb+srv://
user = myUser
pwd = MyPassword123
dbUrl = cluster0.abcd1.mongodb.net
dbName = cloudProjectDB
params = ?retryWrites=true&w=majority&appName=CloudProject
```

---

## ▶️ Running the Server

```bash
python3 app.py
```

Server runs at:

```
http://127.0.0.1:5001
```

---

# 📌 API Documentation

---

## 🟢 1. Signup

**POST /signup**

### Request Body

```json
{
  "username": "john",
  "password": "123456"
}
```

### Response

```json
{
  "message": "User created",
  "user_id": "uuid"
}
```

---

## 🟢 2. Login

**POST /login**

### Request Body

```json
{
  "username": "john",
  "password": "123456"
}
```

### Response

```json
{
  "message": "Login successful",
  "session_id": "xxxxxxxx-xxxx"
}
```

---

## 🟢 3. Convert Currency

**POST /convert**

### Headers

```
session_id: your-session-id
```

### Body

```json
{
  "base_country": "United States",
  "target_country": "Japan",
  "amount": 100
}
```

### Response

```json
{
  "record_id": "uuid",
  "base": "USD",
  "target": "JPY",
  "rate": 150.45,
  "converted_amount": 15045,
  "date": "2025-11-18"
}
```

---

## 🟢 4. Get Conversion History

**GET /records**

### Headers

```
session_id: your-session-id
```

### Response

```json
[
  {
    "record_id": "uuid",
    "base": "USD",
    "target": "JPY",
    "amount": 100,
    "converted_amount": 15045,
    "rate": 150.45,
    "date": "2025-11-18"
  }
]
```

---

## ⚠️ Error Responses

Missing session:

```json
{"error": "Session expired or invalid"}
```

Missing fields:

```json
{"error": "Missing base_country or target_country"}
```

Frankfurter API down:

```json
{"error": "Currency API unavailable"}
```

---

# 🧪 Testing with Postman

### 1. Signup

POST → `http://127.0.0.1:5001/signup`

### 2. Login

POST → `http://127.0.0.1:5001/login`
Copy the `session_id`

### 3. Convert

POST → `http://127.0.0.1:5001/convert`
Header:

```
session_id: {YOUR_SESSION}
```

### 4. Records

GET → `http://127.0.0.1:5001/records`
Header:

```
session_id: {YOUR_SESSION}
```

---

# 🏁 Done!

If you want, I can also generate:

✅ `requirements.txt`
✅ Full final `app.py` (if not yet final)
✅ Diagram (System Architecture)
✅ Video-ready explanation
✅ API documentation (Swagger)

Just tell me!
