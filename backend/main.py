import os
import io
import uuid
import time  
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
import google.generativeai as genai  # 🧠 Google Gemini SDK

app = FastAPI()

# CORS Setting
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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Google Gemini AI Setup
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 🤖 TELEGRAM CONFIGURATION
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "YOUR_TELEGRAM_BOT_TOKEN"

# 🔒 SECURITY: Nimma personal Telegram Chat ID
JEEVAN_TELEGRAM_CHAT_ID = 2113728041

# 📱 Jeevan nimma personal WhatsApp number (Ega idakkile chat test madthidivi)
YOUR_PERSONAL_PHONE = "917411255628"

# 👥 WhatsApp Group ID (Sadyakke idanna use madthilla, personal chat ge hogutthe)
WHATSAPP_GROUP_ID = os.getenv("WHATSAPP_GROUP_ID") or "YOUR_WHATSAPP_GROUP_ID@g.us"

# 💳 UPI ID 
YOUR_UPI_ID = "7411255628@ybl"  

# 📸 Instagram API
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

# ─── 📨 WHATSAPP MESSAGE FUNCTION ───
def send_whatsapp(phone, message):
    if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
        print("❌ Green API Credentials Missing!")
        return False
    
    phone = str(phone).replace("+", "").replace(" ", "").strip()
    if len(phone) == 10:
        phone = f"91{phone}"
        
    chat_id = phone if phone.endswith("@c.us") else f"{phone}@c.us"
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
    
    try:
        response = requests.post(url, json={"chatId": chat_id, "message": message}, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ WhatsApp Send Exception: {str(e)}")
        return False

# ─── 🧠 SMART GEMINI AI FUNCTION (NAME, CATEGORY & DESCRIPTION GENERATOR) ───
def generate_product_details_via_ai(image_url):
    """Photo nodi automatic agi Name, Category mathu Description create madutthe"""
    try:
        if not GOOGLE_API_KEY:
            return "Trending Designer Wear", "Kurti", "Exclusively curated premium collection at Dolphin Trends."
            
        response = requests.get(image_url)
        image_bytes = response.content
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "Analyze this fashion clothing image for an online boutique named Dolphin Trends. "
            "1. Provide a beautiful, trendy, and catchy product name (e.g., 'Elegant Floral Georgette Anarkali'). "
            "2. Identify the category in one or two words maximum (e.g., 'Kurti', 'Saree', 'Lehenga', 'Gown', 'Western Wear'). "
            "3. Provide a short, attractive boutique description (1-2 sentences) praising the fabric and style. "
            "Strictly return the response in exactly this format without any other words: Name | Category | Description"
        )
        
        cookie_img = {"mime_type": "image/jpeg", "data": image_bytes}
        ai_response = model.generate_content([prompt, cookie_img])
        
        text_res = ai_response.text.strip()
        print(f"🤖 Gemini AI Output: {text_res}")
        
        if "|" in text_res:
            parts = text_res.split("|")
            name = parts[0].strip()
            category = parts[1].strip()
            desc = parts[2].strip()
            return name, category, desc
            
        return "Exclusive Boutique Wear", "Uncategorized", "Premium quality outfit specially selected for you."
    except Exception as e:
        print(f"❌ Gemini AI Error: {str(e)}")
        return "New Fashion Arrival", "Kurti", "Beautiful design crafted with rich fabric and premium finishing."

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
        
        admin_message = (
            f"🔔 *New Booking Alert!* 🔔\n\n"
            f"Hi Jeevan, a customer has just placed an order request on the website.\n\n"
            f"👤 *Customer:* {payload.customer_name}\n"
            f"👗 *Product:* {payload.product_name}\n\n"
            f"🔗 *Admin Dashboard:* https://dolphin-trends-two.vercel.app"
        )
        send_whatsapp(YOUR_PERSONAL_PHONE, admin_message)
        
        customer_waiting_message = (
            f"Hi {payload.customer_name},\n\n"
            f"Thank you for visiting Dolphin Trends! 🐬✨\n\n"
            f"Your booking request for *{payload.product_name}* has been registered. "
            f"Our team is currently verifying stock availability. Please wait 5 minutes! 🙏"
        )
        send_whatsapp(payload.customer_phone, customer_waiting_message)
        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── 🤖 2. JEEVAN MASTER AUTOMATED WEBHOOK (WITH CHAT ID & CUSTOM CATEGORY LOGIC) ───
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
                requests.post(send_url, json={"chat_id": chat_id, "text": "Welcome to Dolphin Trends! 🐬"})
                return {"status": "Unauthorized user ignored"}

            if "photo" in message:
                caption = message.get("caption", "").strip()
                file_id = message["photo"][-1]["file_id"]
                
                file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
                file_info = requests.get(file_info_url).json()
                file_path = file_info.get("result", {}).get("file_path")

                if not file_path:
                    return {"status": "Image path error"}

                public_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                
                # Default variables set madೋಣ
                product_name = "New Trendy Arrival"
                product_price = "₹1500"
                product_category = "Kurti"
                product_description = "Exclusively curated collection at Dolphin Trends."
                
                # ─── 🗂️ CATEGORY, NAME & PRICE CONDITION CHECK ───
                if caption:
                    clean_caption = caption.replace("₹", "").replace(",", "").strip()
                    
                    # Scenario A: User bari Price mathra kalsidre (e.g., 1200)
                    if clean_caption.isdigit():
                        product_price = f"₹{clean_caption}"
                        print(f"💰 Custom price detected: {product_price}. Generating rest via AI...")
                        product_name, product_category, product_description = generate_product_details_via_ai(public_image_url)
                        
                    # Scenario B: User manually formatting kalsidre (Name - Price - Category)
                    elif "-" in caption:
                        parts = caption.split("-")
                        if len(parts) >= 3:
                            product_name = parts[0].strip()
                            product_price = parts[1].strip()
                            product_category = parts[2].strip()
                            if len(parts) > 3:
                                product_description = parts[3].strip()
                            print("📝 Custom Name, Price & Category detected manually.")
                        elif len(parts) == 2:
                            product_name = parts[0].strip()
                            product_price = parts[1].strip()
                            # Category AI inda barutte
                            _, product_category, product_description = generate_product_details_via_ai(public_image_url)
                        
                        if not product_price.startswith("₹"):
                            product_price = f"₹{product_price}"
                    
                    # Scenario C: Text ide adre format illa andre adanna Name ankoni mikkiddu AI text generate mado logic
                    else:
                        product_name = caption
                        _, product_category, product_description = generate_product_details_via_ai(public_image_url)
                
                # Scenario D: Caption khali idre pūrthi AI generate mado logic
                else:
                    print("🔮 Photo only detected. Full AI Automation Mode Active...")
                    product_name, product_category, product_description = generate_product_details_via_ai(public_image_url)

                # 🌐 A. WEBSITE PRODUCT ADD (MongoDB table updates with category)
                new_product_id = str(uuid.uuid4())[:6]
                product_data = {
                    "product_id": new_product_id,
                    "name": product_name,
                    "price": product_price,
                    "category": product_category,
                    "image": public_image_url,
                    "description": product_description
                }
                products_table.insert_one(product_data)

                # 📱 B. DIRECT TO YOUR PERSONAL WHATSAPP CHAT ID (Testing purpose)
                whatsapp_personal_msg = (
                    f"👗 *NEW ARRIVAL LIVE ON WEBSITE!* 👗\n\n"
                    f"Hi Jeevan, your product setup details:\n\n"
                    f"✨ *Name:* {product_name}\n"
                    f"🗂️ *Category:* {product_category}\n"
                    f"💰 *Price:* {product_price}\n"
                    f"📝 *Description:* {product_description}\n\n"
                    f"🔗 *Website URL:* https://dolphin-trends-two.vercel.app"
                )
                
                wa_url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
                
                # 🎯 WhatsApp Chat ID setup: `YOUR_PERSONAL_PHONE` ge hogutthe
                wa_payload = {
                    "chatId": f"{YOUR_PERSONAL_PHONE}@c.us", 
                    "urlFile": public_image_url,
                    "fileName": f"product_{new_product_id}.jpg",
                    "caption": whatsapp_personal_msg
                }
                requests.post(wa_url, json=wa_payload, timeout=10)

                # 📸 C. INSTAGRAM POSTING
                if INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN:
                    try:
                        ig_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}/media"
                        ig_payload = {
                            "image_url": public_image_url,
                            "caption": f"✨ New Arrival: {product_name} ✨\n\nCategory: {product_category}\nPrice: {product_price}\n\n{product_description}\n\nAvailable now on our website! 🥰",
                            "access_token": INSTAGRAM_ACCESS_TOKEN
                        }
                        ig_res = requests.post(ig_url, data=ig_payload).json()
                        creation_id = ig_res.get("id")
                        if creation_id:
                            publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
                            requests.post(publish_url, data={"creation_id": creation_id, "access_token": INSTAGRAM_ACCESS_TOKEN})
                    except Exception as ig_err:
                        print("❌ Instagram Post Error:", str(ig_err))

                # 💬 D. TELEGRAM RETURN MESSAGE WITH CLICKABLE BLUE LINK
                reply_text = (
                    f"✅ *Hi Jeevan! Product successfully uploaded to:*\n\n"
                    f"1. Website Catalog 🌐 (Category: {product_category})\n"
                    f"2. Personal WhatsApp Chat 📱 (Chat ID Active)\n"
                    f"3. Instagram Feed 📸\n\n"
                    f"🔗 *Live Website:* https://dolphin-trends-two.vercel.app"
                )
                send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(send_url, json={
                    "chat_id": chat_id, 
                    "text": reply_text,
                    "parse_mode": "Markdown"
                })

        return {"status": "success"}
    except Exception as e:
        print("Webhook Master Error:", str(e))
        return {"status": "error"}

# ─── 🟢 🔴 🔵 3. ADMIN PANEL CODES ───
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
            
            first_msg = (
                f"Hello {c_name},\n\n"
                f"Great news! The item (*{p_name}*) is AVAILABLE and reserved for you at Dolphin Trends! 🎉👗\n\n"
                f"💰 *Price Details:*\n"
                f"• Total Price: ₹{full_price:.2f}\n"
                f"• Balance to Pay at Shop: ₹{remaining_amount:.2f}\n\n"
                f"🏪 *Our Store Location:* http://maps.google.com\n"
                f"Please visit our store to explore more! 🐬"
            )
            send_whatsapp(c_phone, first_msg)
            time.sleep(3)
            
            second_msg = (
                f"✨ *Want to secure this order?*\n\n"
                f"If you want to confirm your order request, please pay a 50% advance amount (*₹{advance_amount:.2f}*) using the link below.\n\n"
                f"🔗 *Pay Securely via UPI:* {payment_link}\n\n"
                f"📌 *Note:* If you prefer to check directly at store, please *JUST IGNORE* this link! 🙏"
            )
            send_whatsapp(c_phone, second_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved-WaitingPayment"}})
            return {"status": "success"}
            
        elif action == "disagree":
            cust_msg = f"Hello {c_name},\n\nSorry, the product *{p_name}* is currently *Out of Stock*. We will restock soon! 🙏"
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})
            return {"status": "success"}
            
        elif action == "size_unavail":
            cust_msg = f"Hello {c_name},\n\nRegarding *{p_name}*, your selected *Size is currently unavailable*. Please visit store for alternatives! 🐬"
            send_whatsapp(c_phone, cust_msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Size Unavailable"}})
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/bookings")
def get_all_bookings():
    return list(bookings_table.find({}, {"_id": 0})) if bookings_table is not None else []

@app.get("/products")
def get_products():
    return list(products_table.find({}, {"_id": 0})) if products_table is not None else []

@app.get("/")
def home():
    return {"status": "Dolphin Trends Pure Smart AI Backend is Running!"}

# ─── 🔌 MAIN SERVER RUN LOGIC ───
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
