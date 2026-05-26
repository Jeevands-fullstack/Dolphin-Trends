import os
import io
import uuid
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
from PIL import Image

app = FastAPI()

# CORS Setting - Website connect madoke
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ⚙️ CONFIGURATION & CONNECTIONS ───
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

# 📱 Jeevan nimma personal WhatsApp number (Alerts baroke)
YOUR_PERSONAL_PHONE = "917411255628"
# 💳 Nimma asli UPI ID illi haaki (Dynamic payment link ge)
YOUR_UPI_ID = "7411255628@ybl"  

ca = certifi.where()
db = None
bookings_table = None
products_table = None

if MONGO_URL:
    client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=2000, serverSelectionTimeoutMS=2000)
    db = client["dolphin_trends_db"]
    products_table = db["products"]
    bookings_table = db["bookings"]

# ─── 📨 WHATSAPP MESSAGE FUNCTION (GREEN API) ───
def send_whatsapp(phone, message):
    if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
        print("❌ Green API Credentials Missing!")
        return False
    
    phone = str(phone).replace("+", "").replace(" ", "")
    if not phone.endswith("@c.us"):
        chat_id = f"{phone}@c.us"
    else:
        chat_id = phone

    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": message
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"✅ WhatsApp message sent to {phone}")
            return True
        else:
            print(f"❌ WhatsApp API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ WhatsApp Send Exception: {str(e)}")
        return False

# ─── 👗 DATA MODELS ───
class BookingPayload(BaseModel):
    customer_name: str
    customer_phone: str
    product_name: str
    image_url: str

# ─── 🚀 1. CUSTOMER "BUY NOW" SUBMIT API ───
@app.post("/api/bookings")
def create_booking(payload: BookingPayload):
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="Database connection missing")
    
    try:
        booking_id = str(uuid.uuid4())[:8] # Unique 8 letter ID
        
        booking_data = {
            "booking_id": booking_id,
            "customer_name": payload.customer_name,
            "customer_phone": payload.customer_phone,
            "product_name": payload.product_name,
            "image_url": payload.image_url,
            "status": "Pending"
        }
        bookings_table.insert_one(booking_data)
        
        # 🚨 Jeevan nimma personal WhatsApp ge baro simple alert message
        admin_message = f"🚨 *Dolphin Trends Alert!*\n\nHosa Booking bandide, dayavittu website check madi update madi!"
        send_whatsapp(YOUR_PERSONAL_PHONE, admin_message)
        
        # 💬 Customer ge thaxna hogo Instant Waiting Message
        customer_waiting_message = (
            f"Hello {payload.customer_name} ma'am! ✨\n\n"
            f"Nimma order booking successfully register aagide. 👗\n"
            f"Dayavittu 5 minutes wait madi, naavu namma shopalli (Dolphin Trends) "
            f"stock check madi thaxna idhe WhatsApp number ge confirm message kalsthivi. 🙏"
        )
        send_whatsapp(payload.customer_phone, customer_waiting_message)
        
        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── 📋 2. ADMIN PANEL GE DATA DISPLAY MADO API ───
@app.get("/api/admin/bookings")
def get_all_bookings():
    if bookings_table is None:
        return []
    try:
        bookings = list(bookings_table.find({}, {"_id": 0}))
        return bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── 🟢 🔴 3. ADMIN PANEL IND AGREE / DISAGREE MADO API ───
@app.post("/api/admin/update-booking")
def update_booking_status(booking_id: str, action: str):
    if bookings_table is None or products_table is None:
        raise HTTPException(status_code=500, detail="Database connection missing")
        
    try:
        booking = bookings_table.find_one({"booking_id": booking_id})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
            
        c_name = booking["customer_name"]
        c_phone = booking["customer_phone"]
        p_name = booking["product_name"]
        
        if action == "agree":
            # Database ind product price huduki 50% calculate mado logic ⚡
            product = products_table.find_one({"name": p_name})
            full_price = float(product.get("price", 0)) if product else 0
            
            advance_amount = full_price / 2
            remaining_amount = full_price - advance_amount
            
            # 🛡️ Fake Screenshot stop madoke Exact Amount Lock mado Dynamic UPI Intent URL
            merchant_name = "Dolphin%20Trends"
            payment_link = f"upi://pay?pa={YOUR_UPI_ID}&pn={merchant_name}&am={advance_amount:.2f}&cu=INR"
            
            # 🟢 Stock ide - WhatsApp message with 50% price detail & QR-Link
            cust_msg = (
                f"ಹಲೋ {c_name} ಮಾಮ್, ನೀವು ಬುಕ್ ಮಾಡಿದ ಡ್ರೆಸ್ (*{p_name}*) ನಮ್ಮ Dolphin Trends ಶಾಪಲ್ಲಿ ರೆಡಿ ಇದೆ! 👗✨\n\n"
                f"💰 *Price Details:*\n"
                f"• Total Price: ₹{full_price:.2f}\n"
                f"• *Advance to Pay (50%): ₹{advance_amount:.2f}*\n"
                f"• Balance at Shop: ₹{remaining_amount:.2f}\n\n"
                f"📢 *Note:* Nimige product confirm beku ansidre, kelagina link click madi exact ₹{advance_amount:.2f} advance payment madi order confirm madkoli. "
                f"Aavaga shop ge baro vasthige ee batte bere yarigoo sale aagalla!\n\n"
                f"🔗 *Pay via GPay/PhonePe Link:* {payment_link}\n\n"
                f"Illa andre just ignore it and visit our shop. Thank you! 🙏"
            )
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved-WaitingPayment"}})
            return {"status": "success", "message": "Approved & 50% payment link sent!"}
            
        elif action == "disagree":
            # 🔴 Out of Stock Message
            cust_msg = f"Sorry {c_name} ಮಾಮ್, ನೀವು ಕೇಳಿದ ಡ್ರೆಸ್ ಸದ್ಯಕ್ಕೆ Out of Stock ಆಗಿದೆ. ಸ್ವಲ್ಪ ದಿನದಲ್ಲೇ ಮತ್ತೆ ತರಿಸ್ತೀವಿ. Dolphin Trends ಗೆ ಭೇಟಿ ನೀಡಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು! 🙏"
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})
            return {"status": "success", "message": "Disapproved & Out of stock message sent"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── ⚡ PRODUCTS FETCH FOR WEBSITE ───
@app.get("/api/products")
def get_products():
    if products_table is None:
        return []
    try:
        products = list(products_table.find({}, {"_id": 0}))
        return products
    except Exception as e:
        print("MongoDB Fetch Error:", str(e))
        return []

@app.get("/")
def home():
    return {"status": "Dolphin Trends Super Automated Backend is Running!"}
