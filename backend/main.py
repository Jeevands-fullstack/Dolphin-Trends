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

# CORS Setting - ವೆಬ್‌ಸೈಟ್ ಕನೆಕ್ಟ್ ಮಾಡೋಕೆ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ⚙️ ಕಾನ್ಫಿಗರೇಶನ್ ಮತ್ತು ಕನೆಕ್ಷನ್ಸ್ ───
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

# 📱 ಜೀವನ್ ನಿಮ್ಮ ಪರ್ಸನಲ್ ವಾಟ್ಸಾಪ್ ನಂಬರ್ (ಅಲರ್ಟ್ ಬರಲು)
YOUR_PERSONAL_PHONE = "917411255628"

ca = certifi.where()
db = None
bookings_table = None

if MONGO_URL:
    # ⚡ ಕನೆಕ್ಷನ್ ಟೈಮ್‌ಔಟ್ 2 ಸೆಕೆಂಡ್‌ಗೆ ಸೆಟ್ ಮಾಡಲಾಗಿದೆ (ವೆಬ್‌ಸೈಟ್ ಸ್ಲೋ ಆಗಲ್ಲ!)
    client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=2000, serverSelectionTimeoutMS=2000)
    db = client["dolphin_trends_db"]
    products_table = db["products"]
    bookings_table = db["bookings"] # ಹೊಸ ಬುಕಿಂಗ್ ಟೇಬಲ್

# ─── 📨 ವಾಟ್ಸಾಪ್ ಮೆಸೇಜ್ ಕಳುಹಿಸುವ ಫಂಕ್ಷನ್ (GREEN API) ───
def send_whatsapp(phone, message):
    if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
        print("❌ Green API Credentials Missing!")
        return False
    
    # ನಂಬರ್ ಕ್ಲೀನ್ ಮಾಡೋದು (ಸ್ಪೇಸ್ ಅಥವಾ + ಇದ್ದರೆ ರಿಮೂವ್ ಮಾಡುತ್ತೆ)
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

# ─── 👗 ಕಸ್ಟಮರ್ ಆರ್ಡರ್ ಬುಕಿಂಗ್ ಮಾಡೆಲ್ ───
class BookingPayload(BaseModel):
    customer_name: str
    customer_phone: str
    product_name: str
    image_url: str

# 1. 📥 ಕಸ್ಟಮರ್ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ "Buy Now" ಸಬ್ಮಿಟ್ ಮಾಡಿದಾಗ ರನ್ ಆಗುವ ಏಪಿಐ
@app.post("/api/bookings")
def create_booking(payload: BookingPayload):
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="Database connection missing")
    
    try:
        booking_id = str(uuid.uuid4())[:8] # ಯುನಿಕ್ 8 ಅಕ್ಷರದ ಬುಕಿಂಗ್ ಐಡಿ
        
        booking_data = {
            "booking_id": booking_id,
            "customer_name": payload.customer_name,
            "customer_phone": payload.customer_phone,
            "product_name": payload.product_name,
            "image_url": payload.image_url,
            "status": "Pending"
        }
        bookings_table.insert_one(booking_data)
        
        # 🚨 ಜೀವನ್ ನಿಮ್ಮ ವಾಟ್ಸಾಪ್‌ಗೆ ಬರುವ ಸಿಂಪಲ್ ಅಲರ್ಟ್ ಮೆಸೇಜ್
        admin_message = f"🚨 *Dolphin Trends Alert!*\n\nಹೊಸ Booking ಬಂದಿದೆ, ದಯವಿಟ್ಟು ವೆಬ್‌ಸೈಟ್ ಅಪ್ಡೇಟ್ ಮಾಡಿ!"
        send_whatsapp(YOUR_PERSONAL_PHONE, admin_message)
        
        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. 📋 ವೆಬ್‌ಸೈಟ್ ಅಡ್ಮಿನ್ ಪ್ಯಾನೆಲ್‌ಗೆ ಎಲ್ಲಾ ಬುಕಿಂಗ್ ಡೇಟಾ ಕಳುಹಿಸುವ ಏಪಿಐ
@app.get("/api/admin/bookings")
def get_all_bookings():
    if bookings_table is None:
        return []
    try:
        bookings = list(bookings_table.find({}, {"_id": 0}))
        return bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. 🟢 🔴 ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ನೀವು Agree / Disagree ಕನ್‌ಫರ್ಮ್ ಮಾಡಿದಾಗ ರನ್ ಆಗುವ ಏಪಿಐ
@app.post("/api/admin/update-booking")
def update_booking_status(booking_id: str, action: str):
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="Database connection missing")
        
    try:
        booking = bookings_table.find_one({"booking_id": booking_id})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
            
        c_name = booking["customer_name"]
        c_phone = booking["customer_phone"]
        
        if action == "agree":
            # 🟢 ಸ್ಟಾಕ್ ಇದೆ - ಕಸ್ಟಮರ್ ವಾಟ್ಸಾಪ್‌ಗೆ ಮೆಸೇಜ್
            cust_msg = f"ಹಲೋ {c_name} ಮಾಮ್, ನೀವು ಬುಕ್ ಮಾಡಿದ ಡ್ರೆಸ್ ನಮ್ಮ Dolphin Trends ಶಾಪಲ್ಲಿ ರೆಡಿ ಇದೆ. ದಯವಿಟ್ಟು ಬೇಗ ಶಾಪ್‌ಗೆ ಬಂದು ಕಲೆಕ್ಟ್ ಮಾಡಿಕೊಳ್ಳಿ. ಧನ್ಯವಾದಗಳು! 👗✨"
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved"}})
            return {"status": "success", "message": "Approved & WhatsApp Sent"}
            
        elif action == "disagree":
            # 🔴 ಔಟ್ ಆಫ್ ಸ್ಟಾಕ್ - ಕಸ್ಟಮರ್ ವಾಟ್ಸಾಪ್‌ಗೆ ಮೆಸೇಜ್
            cust_msg = f"Sorry {c_name} ಮಾಮ್, ನೀವು ಕೇಳಿದ ಡ್ರೆಸ್ ಸದ್ಯಕ್ಕೆ Out of Stock ಆಗಿದೆ. ಸ್ವಲ್ಪ ದಿನದಲ್ಲೇ ಮತ್ತೆ ತರಿಸ್ತೀವಿ. ನಮ್ಮ ವೆಬ್‌ಸೈಟ್‌ಗೆ ವیسیಟ್ ಮಾಡಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು! 🙏"
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})
            return {"status": "success", "message": "Disapproved & WhatsApp Sent"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── ⚡ ಒರಿಜಿನಲ್ ವೆಬ್‌ಸೈಟ್ ಪ್ರಾಡಕ್ಟ್ಸ್ ಏಪಿಐ ───
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
    return {"status": "Dolphin Trends API is Running Super Fast!"}
