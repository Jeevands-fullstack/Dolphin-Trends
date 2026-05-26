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
        
        # 🚨 1. NIMGE (ADMIN) BARO AUTOMATIC MESSAGE WITH WEBSITE LINK
        admin_message = (
            f"🔔 *New Booking Alert!* 🔔\n\n"
            f"Hi Jeevan, a customer has just placed an order request on the website. Please review it in the admin panel.\n\n"
            f"👤 *Customer:* {payload.customer_name}\n"
            f"👗 *Product:* {payload.product_name}\n\n"
            f"🔗 *Admin Dashboard:* https://dolphin-trends-two.vercel.app"
        )
        send_whatsapp(YOUR_PERSONAL_PHONE, admin_message)
        
        # 💬 2. CUSTOMER GE TAXNA HOGO PROFESSIONAL WAITING MESSAGE
        customer_waiting_message = (
            f"Hi {payload.customer_name},\n\n"
            f"Thank you for visiting Dolphin Trends! 🐬✨\n\n"
            f"Your booking request for *{payload.product_name}* has been successfully registered. "
            f"Our team is currently verifying the stock availability at our store.\n\n"
            f"Please give us about 5 minutes. We will send you a confirmation message right here shortly. Thank you for your patience! 🙏"
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
            
            # Cleaning price string (eg: "₹350" -> 350.0)
            full_price = 0.0
            if product and "price" in product:
                try:
                    price_str = str(product["price"]).replace("₹", "").replace(",", "").strip()
                    full_price = float(price_str)
                except:
                    full_price = 0.0
            
            advance_amount = full_price / 2
            remaining_amount = full_price - advance_amount
            
            # 🛡️ Fake Screenshot stop madoke Exact Amount Lock mado Dynamic UPI Intent URL
            merchant_name = "Dolphin%20Trends"
            payment_link = f"upi://pay?pa={YOUR_UPI_ID}&pn={merchant_name}&am={advance_amount:.2f}&cu=INR"
            
            # 🟢 1. CUSTOMER GE HOGO PROFESSIONAL AGREE MESSAGE WITH LOCATION & DETAILS
            cust_msg = (
                f"Hello {c_name},\n\n"
                f"Great news! The item you selected (*{p_name}*) is AVAILABLE and reserved for you at Dolphin Trends! 🎉👗\n\n"
                f"💰 *Price & Order Details:*\n"
                f"• Total Price: ₹{full_price:.2f}\n"
                f"• *Advance to Secure (50%): ₹{advance_amount:.2f}*\n"
                f"• Balance to Pay at Shop: ₹{remaining_amount:.2f}\n\n"
                f"✨ *How to Confirm Your Order:*\n"
                f"If you absolutely love this product and want to secure it, please click the secure link below to pay the 50% advance amount. Once paid, this item will be completely locked for you and won't be sold to anyone else!\n"
                f"🔗 *Pay Securely via GPay/PhonePe:* {payment_link}\n\n"
                f"📌 *Prefer to check it out first?*\n"
                f"If you prefer not to pay online, please feel free to ignore the payment link and directly visit our store to explore and buy!\n\n"
                f"🏪 *Store Location:* https://maps.app.goo.gl/vYm66S8mGz7K7uCH7 (Laggere Main Road, Bangalore)\n\n"
                f"Thank you for choosing Dolphin Trends! We look forward to seeing you. 🐬"
            )
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved-WaitingPayment"}})
            return {"status": "success", "message": "Approved & Professional WhatsApp message sent!"}
            
        elif action == "disagree":
            # 🔴 2. CUSTOMER GE HOGO PROFESSIONAL OUT OF STOCK MESSAGE
            cust_msg = (
                f"Hello {c_name},\n\n"
                f"Thank you for your interest in Dolphin Trends. 🌸\n\n"
                f"We are very sorry, but the product you requested (*{p_name}*) is currently *Out of Stock* due to high demand. "
                f"We expect to restock this collection very soon!\n\n"
                f"We highly appreciate your visit to our website and hope to welcome you to our physical store soon to explore other fresh designs.\n\n"
                f"Warm regards,\n"
                f"Team Dolphin Trends, Bangalore. 🙏"
            )
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})
            return {"status": "success", "message": "Disapproved & Out of stock message sent"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── ⚡ PRODUCTS FETCH FOR WEBSITE ───
@app.get("/products")
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
