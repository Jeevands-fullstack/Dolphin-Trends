import os
import io
import uuid
import time  # ⏳ 3 Seconds gap kodoke time module add madiroodu
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

# 🤖 TELEGRAM CONFIGURATION
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"
WHATSAPP_GROUP_ID = os.getenv("WHATSAPP_GROUP_ID") or "YOUR_WHATSAPP_GROUP_ID@g.us"

# 🔒 SECURITY: Nimma personal Telegram Chat ID ಹಾಕಿ ಜೀವನ್
JEEVAN_TELEGRAM_CHAT_ID = 7411255628  

# 📱 Jeevan nimma personal WhatsApp number (Alerts baroke)
YOUR_PERSONAL_PHONE = "917411255628"
# 💳 Nimma asli UPI ID illi haaki (Dynamic payment link ge)
YOUR_UPI_ID = "7411255628@ybl"  

# 📸 Instagram API Credentials (Meta Dashboard ind)
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

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
    
    phone = str(phone).replace("+", "").replace(" ", "").strip()
    
    if len(phone) == 10:
        phone = f"91{phone}"
        
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
        return response.status_code == 200
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
        booking_id = str(uuid.uuid4())[:8]
        
        booking_data = {
            "booking_id": booking_id,
            "customer_name": payload.customer_name,
            "customer_phone": payload.customer_phone,
            "product_name": payload.product_name,
            "image_url": payload.image_url,
            "status": "Pending"
        }
        bookings_table.insert_one(booking_data)
        
        # 🚨 A. NIMGE (ADMIN) BARO AUTOMATIC ALERT
        admin_message = (
            f"🔔 *New Booking Alert!* 🔔\n\n"
            f"Hi Jeevan, a customer has just placed an order request on the website. Please review it in the admin panel.\n\n"
            f"👤 *Customer:* {payload.customer_name}\n"
            f"👗 *Product:* {payload.product_name}\n\n"
            f"🔗 *Admin Dashboard:* https://dolphin-trends-two.vercel.app"
        )
        send_whatsapp(YOUR_PERSONAL_PHONE, admin_message)
        
        # 💬 B. CUSTOMER GE TAXNA HOGO PROFESSIONAL WAITING MESSAGE
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

# ─── 🤖 2. JEEVAN MASTER TELEGRAM AUTOMATION WEBHOOK ───
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if products_table is None:
        return {"status": "Database error"}

    try:
        data = await request.json()
        
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            
            if chat_id != JEEVAN_TELEGRAM_CHAT_ID:
                send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(send_url, json={"chat_id": chat_id, "text": "Welcome to Dolphin Trends! 🐬 Please visit our website: https://dolphin-trends-two.vercel.app"})
                return {"status": "Unauthorized user ignored"}

            if "photo" in message:
                file_id = message["photo"][-1]["file_id"]
                caption = message.get("caption", "New Arrival - Price details upon request")
                
                product_name = caption
                product_price = "₹1500" 
                if "-" in caption:
                    parts = caption.split("-")
                    product_name = parts[0].strip()
                    product_price = parts[1].strip()

                file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
                file_info = requests.get(file_info_url).json()
                file_path = file_info["result"]["file_path"]
                public_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                
                # 1️⃣ WEBSITE PRODUCT ADD (MongoDB)
                new_product_id = str(uuid.uuid4())[:6]
                product_data = {
                    "product_id": new_product_id,
                    "name": product_name,
                    "price": product_price,
                    "image": public_image_url,
                    "description": "Exclusively curated collection at Dolphin Trends."
                }
                products_table.insert_one(product_data)

                # 2️⃣ WHATSAPP GROUP SHARE
                whatsapp_group_msg = (
                    f"👗 *NEW ARRIVAL ALERT!* 👗\n\n"
                    f"Hello Ladies! Check out our latest collection just added to our store.\n\n"
                    f"✨ *Product:* {product_name}\n"
                    f"💰 *Price:* {product_price}\n\n"
                    f"Hurry up! Tap the link below to book yours before it sells out! 👇\n"
                    f"🔗 *Website:* https://dolphin-trends-two.vercel.app"
                )
                
                wa_url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
                wa_payload = {
                    "chatId": WHATSAPP_GROUP_ID,
                    "urlFile": public_image_url,
                    "fileName": f"product_{new_product_id}.jpg",
                    "caption": whatsapp_group_msg
                }
                requests.post(wa_url, json=wa_payload, timeout=10)

                # 3️⃣ INSTAGRAM POSTING
                if INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN:
                    try:
                        ig_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}/media"
                        ig_payload = {
                            "image_url": public_image_url,
                            "caption": f"✨ New Arrival ✨\n\nFeatured: {product_name}\nPrice: {product_price}\n\nAvailable now on our website! Link in bio. 🥰 #dolphintrends #bangalorefashion #boutique",
                            "access_token": INSTAGRAM_ACCESS_TOKEN
                        }
                        ig_res = requests.post(ig_url, data=ig_payload).json()
                        creation_id = ig_res.get("id")
                        
                        if creation_id:
                            publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
                            requests.post(publish_url, data={"creation_id": creation_id, "access_token": INSTAGRAM_ACCESS_TOKEN})
                    except Exception as ig_err:
                        print("❌ Instagram Post Error:", str(ig_err))

                reply_text = f"✅ Hi Jeevan! Product successfully uploaded to:\n1. Website Catalog 🌐\n2. WhatsApp Group 📱\n3. Instagram Feed 📸"
                send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(send_url, json={"chat_id": chat_id, "text": reply_text})

        return {"status": "success"}
    except Exception as e:
        print("Webhook Master Error:", str(e))
        return {"status": "error"}

# ─── 🟢 🔴 🔵 3. ADMIN PANEL IND AGREE / DISAGREE / SIZE UNAVAILABLE API ───
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
        
        # 🟢 ಆಪ್ಷನ್ 1: AGREE CLICK MADIDAGA (SPLIT MESSAGE WITH 3 SEC DELAY)
        if action == "agree":
            product = products_table.find_one({"name": p_name})
            full_price = 0.0
            if product and "price" in product:
                try:
                    price_str = str(product["price"]).replace("₹", "").replace(",", "").strip()
                    full_price = float(price_str)
                except:
                    full_price = 0.0
            
            advance_amount = full_price / 2
            remaining_amount = full_price - advance_amount
            
            merchant_name = "Dolphin%20Trends"
            payment_link = f"upi://pay?pa={YOUR_UPI_ID}&pn={merchant_name}&am={advance_amount:.2f}&cu=INR"
            
            # 📱 MESSAGE 1: BARI PRODUCT DETAILS & SHOP LOCATION
            first_msg = (
                f"Hello {c_name},\n\n"
                f"Great news! The item you selected (*{p_name}*) is AVAILABLE and reserved for you at Dolphin Trends! 🎉👗\n\n"
                f"💰 *Price Details:*\n"
                f"• Total Price: ₹{full_price:.2f}\n"
                f"• Balance to Pay at Shop: ₹{remaining_amount:.2f}\n\n"
                f"🏪 *Our Store Location:* https://maps.app.goo.gl/vYm66S8mGz7K7uCH7 (Laggere Main Road, Bangalore)\n\n"
                f"Please visit our store to explore more collections! 🐬"
            )
            # Modala message send agutthe
            send_whatsapp(c_phone, first_msg)
            
            # ⏳ EXACT 3 SECONDS WAIT
            time.sleep(3)
            
            # 📱 MESSAGE 2: PAYMENT NOTE WITH ADVANCE BOOKING (ISTA IDRE MADI / JUST IGNORE)
            second_msg = (
                f"✨ *Want to secure this order?*\n\n"
                f"If you absolutely love this product and want to confirm your order request, please pay a 50% advance amount (*₹{advance_amount:.2f}*) using the link below. "
                f"Once paid, this item will be completely locked for you and you can come to the shop and collect it! 🥰\n\n"
                f"🔗 *Pay Securely via UPI:* {payment_link}\n\n"
                f"📌 *Note:* If you prefer to check the item directly at our store before buying, please *JUST IGNORE* this payment link and visit us directly! 🙏"
            )
            # Eradane message auto-send agutthe 3 seconds nantara
            send_whatsapp(c_phone, second_msg)
            
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved-WaitingPayment"}})
            return {"status": "success", "message": "Split messages sent with 3 seconds delay!"}
            
        # 🔴 ಆಪ್ಷನ್ 2: ಕಂಪ್ಲೀಟ್ ಔಟ್ ಆಫ್  ಸ್ಟಾಕ್ (DISAGREE)
        elif action == "disagree":
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
            
        # 🔵 ಆಪ್ಷನ್ 3: ಬಟ್ಟೆ ಇದೆ ಆದ್ರೆ ಸೈಜ್ ಇಲ್ಲ (SIZE UNAVAILABLE)
        elif action == "size_unavail":
            cust_msg = (
                f"Hello {c_name},\n\n"
                f"Thank you for ordering with Dolphin Trends! 🐬✨\n\n"
                f"Regarding your request for *{p_name}*, we have the item in stock, but unfortunately, your selected *Size is currently unavailable* due to high demand. 🌸\n\n"
                f"🛍️ *What you can do:*\n"
                f"• If you would like to try a different size, please reply directly to this message.\n"
                f"• Alternatively, you are most welcome to visit our store to explore more designs and fresh alternatives!\n\n"
                f"🏪 *Store Location:* https://maps.app.goo.gl/vYm66S8mGz7K7uCH7 (Laggere Main Road, Bangalore)\n\n"
                f"Thank you for your understanding! 🙏\n"
                f"Team Dolphin Trends."
            )
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Size Unavailable"}})
            return {"status": "success", "message": "Size Unavailable message sent to customer!"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── 📋 4. ADMIN PANEL DATA DISPLAY ───
@app.get("/api/admin/bookings")
def get_all_bookings():
    if bookings_table is None:
        return []
    try:
        bookings = list(bookings_table.find({}, {"_id": 0}))
        return bookings
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
