import os
import uuid
import time
import requests
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
import google.generativeai as genai
import cloudinary
import cloudinary.uploader

# 🌐 MongoDB & Global Variables Configuration
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "https://dolphin-trends-3.onrender.com"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

CLOUDINARY_CLOUD_NAME = "diqwkall4"
CLOUDINARY_API_KEY_VAL = os.getenv("CLOUDINARY_API_KEY", "YOUR_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "YOUR_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY_VAL,
    api_secret=CLOUDINARY_API_SECRET
)

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

raw_users = os.getenv("ALLOWED_USERS", "2113728041")
ALLOWED_USERS = [int(uid.strip()) for uid in raw_users.split(",") if uid.strip().isdigit()]

# 📱 3 Personal Phone Numbers & 1 WhatsApp Group ID Setup via Environment Variables
YOUR_PERSONAL_PHONE = "917411255628"  # 1st number hardcoded
SECOND_PERSONAL_PHONE = os.getenv("SECOND_PERSONAL_PHONE", "91XXXXXXXXXX")  # 2nd number from Render
THIRD_PERSONAL_PHONE = os.getenv("THIRD_PERSONAL_PHONE", "91XXXXXXXXXX")    # 3rd number from Render
YOUR_WHATSAPP_GROUP_ID = os.getenv("YOUR_WHATSAPP_GROUP_ID", "120363293847291048@g.us")  # Group ID from Render

# 🔥 Website ನಲ್ಲಿರೋ ಪಕ್ಕಾ ಕ್ಯಾಟಗರಿ ಲಿಸ್ಟ್!
VALID_CATEGORIES = [
    "Leggings", "Kurta Sets", "Jeans", "Patiala Pants", "Kurtha Top", 
    "Umbrella Sets", "Frocks", "Western Wear", "Gym Pants", "250 Tops", 
    "350 Tops", "Jeans Tops"
]

ca = certifi.where()
db = None
bookings_table = None
products_table = None

if MONGO_URL:
    client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
    db = client["dolphin_trends_db"]
    products_table = db["products"]
    bookings_table = db["bookings"]

# 🚀 FastAPI Lifespan Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook")
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": f"{BACKEND_URL}/webhook"}
            )
            print("Webhook set successfully:", r.text)
        except Exception as e:
            print("Webhook setup error during startup:", e)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛠️ Helper Functions
def upload_to_cloudinary(image_source, is_file=False):
    try:
        unique_filename = f"prod_{str(uuid.uuid4())[:8]}"
        result = cloudinary.uploader.upload(
            image_source, 
            folder="dolphin_trends",
            public_id=unique_filename,
            overwrite=True,
            resource_type="image"
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Upload Error: {str(e)}")
        return None

# 🔥 ಈ ಫಂಕ್ಷನ್ ಬರೀ ವಾಟ್ಸಾಪ್ ಗ್ರೂಪ್‌ಗೆ ಮಾತ್ರ ಇಮೇಜ್ ಮತ್ತು ಲಿಂಕ್ ಕಳಿಸುತ್ತೆ
def send_whatsapp_image(image_url, product_name):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
            return False
        caption = (
            f"🔥 *Follow our instagram page and get extra 10% discount👇!* 🐬\n\n"
            f" https://www.instagram.com/dolphin_trends_rajagopalanagar?igsh=MWJ4MGRybGFxOXdiYw==\n\n"
            f"💥 *Explore & order here:* 👇\n"
            f"🔗 {FRONTEND_URL}"
        )
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        
        payload = {
            "chatId": YOUR_WHATSAPP_GROUP_ID,
            "urlFile": image_url,
            "fileName": f"{product_name.replace(' ', '_')}.jpg",
            "caption": caption
        }
        requests.post(url, json=payload, timeout=30)
            
        return True
    except Exception as e:
        print("WhatsApp Image Error:", str(e))
        return False

def send_whatsapp_msg(phone_or_chat_id, message):
    if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
        return False
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
    try:
        if "@g.us" in str(phone_or_chat_id):
            chat_id = phone_or_chat_id
        else:
            phone = str(phone_or_chat_id).replace("+", "").replace(" ", "").strip()
            if len(phone) == 10:
                phone = f"91{phone}"
            chat_id = f"{phone}@c.us"
            
        requests.post(url, json={"chatId": chat_id, "message": message}, timeout=5)
        return True
    except Exception as e:
        print("WhatsApp Msg Error:", str(e))
        return False

def generate_product_details_via_ai(image_url):
    try:
        if not GOOGLE_API_KEY:
            return "Premium Dress", "Western Wear", "Curated boutique wear."
        response = requests.get(image_url)
        image_bytes = response.content
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        categories_str = ", ".join(VALID_CATEGORIES)
        prompt = (
            f"Analyze this boutique fashion clothing image.\n"
            f"1. Provide a simple product name.\n"
            f"2. Select exactly ONE category from this strict list only: [{categories_str}]. Do NOT make up new ones.\n"
            f"3. Short attractive description (1-2 sentences).\n"
            f"Format: Name | Category | Description"
        )
        cookie_img = {"mime_type": "image/jpeg", "data": image_bytes}
        ai_response = model.generate_content([prompt, cookie_img])
        text_res = ai_response.text.strip()
        if "|" in text_res:
            parts = text_res.split("|")
            ai_name = parts[0].strip()
            ai_cat = parts[1].strip()
            ai_desc = parts[2].strip() if len(parts) > 2 else "Beautiful outfit."
            
            matched_cat = "Western Wear"
            for cat in VALID_CATEGORIES:
                if cat.lower() in ai_cat.lower() or ai_cat.lower() in cat.lower():
                    matched_cat = cat
                    break
            return ai_name, matched_cat, ai_desc
            
        return "Premium Dress", "Western Wear", "Beautiful design crafted with rich fabric."
    except Exception as e:
        print("AI Error:", e)
        return "Premium Dress", "Western Wear", "Beautiful design crafted with rich fabric."

# 🛒 Routes
class BookingPayload(BaseModel):
    customer_name: str
    customer_phone: str
    product_name: str
    image_url: str
    size: str = "M"
    price: str = "₹1299"

@app.post("/api/bookings")
def create_booking(payload: BookingPayload):
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="DB Connection Missing")
    try:
        booking_id = str(uuid.uuid4())[:8]
        booking_data = {
            "booking_id": booking_id,
            "customer_name": payload.customer_name,
            "customer_phone": payload.customer_phone,
            "product_name": payload.product_name,
            "image_url": payload.image_url,
            "size": payload.size,
            "price": payload.price,
            "status": "Pending"
        }
        bookings_table.insert_one(booking_data)

        c_phone = str(payload.customer_phone).replace("+", "").replace(" ", "").strip()
        if len(c_phone) == 10:
            c_phone = f"91{c_phone}"

        customer_message = (
            f"🎉 *Welcome to Dolphin Trends!* 🐬\n\n"
            f"Hi {payload.customer_name},\n\n"
            f"You have selected:\n"
            f"👗 *{payload.product_name}*\n"
            f"📏 Size: {payload.size}\n"
            f"💰 Price: {payload.price}\n\n"
            f"📝 *We are currently checking the stock availability for your order. "
            f"Our team will contact you shortly with confirmation.* 🙏\n\n"
            f"💥 *Meanwhile, explore our latest collections here:* 👇\n"
            f"🔗 {FRONTEND_URL}\n\n"
            f"📞 Contact: 9353344035\n\n"
            f"Thank you for choosing us! 😊\n"
            f"*Team Dolphin Trends* 🐬"
        )
        
        send_whatsapp_msg(c_phone, customer_message)

        # 🔥 ನೀನು ಕೇಳಿದ ಹೊಸ "New Buy Request" ಅಲರ್ಟ್ ಫಾರ್ಮ್ಯಾಟ್ ಇಲ್ಲಿದೆ ಬಾಸ್!
        admin_alert = (
            f"🛍️ *New Buy Request!*\n\n"
            f"👗 *Product:* {payload.product_name}\n"
            f"📏 Size: {payload.size}\n"
            f"💰 Price: {payload.price}\n"
            f"👤 Name: {payload.customer_name}\n"
            f"📞 Phone: {payload.customer_phone}\n\n"
            f"⚙️ *Please update here:* 👇\n"
            f"🔗 {FRONTEND_URL}"
        )
        
        # 🎯 ಈ ಮೂರೂ ಪರ್ಸನಲ್ ನಂಬರ್‌ಗಳಿಗೆ ಹೊಸ ಫಾರ್ಮ್ಯಾಟ್‌ನಲ್ಲಿ ಅಲರ್ಟ್ ಹೋಗುತ್ತೆ
        admin_numbers = [YOUR_PERSONAL_PHONE, SECOND_PERSONAL_PHONE, THIRD_PERSONAL_PHONE]
        for num in admin_numbers:
            send_whatsapp_msg(num, admin_alert)

        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products")
async def add_or_update_product_via_panel(
    name: str = Form(...),
    price: str = Form(...),
    original_price: str = Form(None),
    description: str = Form(None),
    category: str = Form(...),
    available: str = Form("true"),
    file: UploadFile = File(None)
):
    if products_table is None:
        raise HTTPException(status_code=500, detail="Database missing")
    try:
        is_available = available.lower() == "true"
        existing_product = products_table.find_one({"name": name, "category": category})
        if not existing_product:
            existing_product = products_table.find_one({"name": name})

        cloud_image_url = None
        if file:
            file_bytes = await file.read()
            if len(file_bytes) > 0:
                cloud_image_url = upload_to_cloudinary(file_bytes, is_file=True)

        if existing_product:
            update_data = {
                "price": price,
                "category": category,
                "description": description or "",
                "available": is_available
            }
            if original_price:
                update_data["original_price"] = original_price
            if cloud_image_url:
                update_data["image"] = cloud_image_url
            products_table.update_one({"_id": existing_product["_id"]}, {"$set": update_data})
            pid = existing_product.get("product_id") or existing_product.get("id", str(existing_product["_id"]))
            return {"status": "success", "action": "updated", "product_id": pid}
        else:
            final_image = cloud_image_url if cloud_image_url else "https://images.unsplash.com/photo-1618932260643-eee4a2f652a6?q=80&w=500"
            new_id = str(uuid.uuid4())[:6]
            product_data = {
                "id": new_id, "product_id": new_id, "name": name, "price": price,
                "original_price": original_price or "", "category": category,
                "description": description or "", "image": final_image,
                "available": is_available
            }
            products_table.insert_one(product_data)
            if cloud_image_url:
                try:
                    send_whatsapp_image(final_image, name)
                except:
                    pass
            return {"status": "success", "action": "created", "product_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def telegram_webhook(request: Request):
    if products_table is None:
        return {"status": "DB error"}
    try:
        data = await request.json()
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            
            if chat_id not in ALLOWED_USERS:
                print(f"Unauthorized Access From: {chat_id}")
                return {"status": "Ignored"}

            if "photo" in message:
                caption = message.get("caption", "").strip()
                file_id = message["photo"][-1]["file_id"]
                file_info = requests.get(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
                    params={"file_id": file_id}
                ).json()
                file_path = file_info.get("result", {}).get("file_path")

                if not file_path:
                    return {"status": "ok"}

                telegram_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                permanent_url = upload_to_cloudinary(telegram_image_url)
                if not permanent_url:
                    permanent_url = telegram_image_url

                product_name = ""
                product_price = ""
                product_category = ""
                product_description = "Curated boutique wear."

                if caption:
                    clean_caption = caption.replace("#edit", "").strip()
                    
                    split_char = None
                    for char in ["-", "–", "—"]:
                        if char in clean_caption:
                            split_char = char
                            break

                    if split_char:
                        parts = clean_caption.split(split_char)
                        if len(parts) >= 1:
                            typed_name = parts[0].strip()
                            product_name = typed_name
                            
                            typed_lower = typed_name.lower().replace(" ", "")
                            typed_singular = typed_lower.rstrip('s') 

                            for cat in VALID_CATEGORIES:
                                cat_lower = cat.lower().replace(" ", "")
                                cat_singular = cat_lower.rstrip('s')
                                
                                if (typed_singular in cat_singular) or (cat_singular in typed_singular):
                                    product_category = cat
                                    break
                            
                            if not product_category:
                                product_category = typed_name
                                
                        if len(parts) >= 2:
                            raw_price = parts[1].strip()
                            if not raw_price.startswith("₹"):
                                product_price = f"₹{raw_price}"
                            else:
                                product_price = raw_price
                    else:
                        price_match = re.search(r'(?:₹\s*)?(\d{3,5})', clean_caption)
                        if price_match:
                            product_price = f"₹{price_match.group(1)}"
                            potential_name = clean_caption.replace(price_match.group(0), "").replace("₹", "").strip()
                            if potential_name:
                                product_name = potential_name
                                
                                typed_lower = potential_name.lower().replace(" ", "").rstrip('s')
                                for cat in VALID_CATEGORIES:
                                    cat_lower = cat.lower().replace(" ", "").rstrip('s')
                                    if (typed_lower in cat_lower) or (cat_lower in typed_lower):
                                        product_category = cat
                                        break
                                if not product_category:
                                    product_category = potential_name

                if not product_price:
                    product_price = "₹1500"

                if not product_name:
                    ai_name, ai_cat, ai_desc = generate_product_details_via_ai(permanent_url)
                    product_name = ai_name
                    product_category = ai_cat
                    if ai_desc:
                        product_description = ai_desc

                new_id = str(uuid.uuid4())[:6]
                products_table.insert_one({
                    "product_id": new_id, "id": new_id,
                    "name": product_name, "price": product_price,
                    "category": product_category, "image": permanent_url,
                    "description": product_description, "available": True
                })

                send_whatsapp_image(permanent_url, product_name)
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": f"✅ Uploaded to {product_category}!\n• Name: {product_name}\n• Price: {product_price}\n• Category: {product_category}\n📲 WhatsApp sent to Group!"}
                )
        return {"status": "success"}
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return {"status": "error"}

@app.put("/api/products/{product_id}")
@app.put("/products/{product_id}")
def update_product_direct(product_id: str, payload: dict):
    if not product_id or product_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid ID")
    result = products_table.update_one({"product_id": product_id}, {"$set": payload})
    if result.matched_count == 0:
        result = products_table.update_one({"id": product_id}, {"$set": payload})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "success"}

@app.delete("/api/products/{product_id}")
@app.delete("/products/{product_id}")
def delete_product_direct(product_id: str):
    if not product_id or product_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid ID")
    result = products_table.delete_one({"product_id": product_id})
    if result.deleted_count == 0:
        products_table.delete_one({"id": product_id})
    return {"success": True}

@app.delete("/api/admin/bookings/{booking_id}")
@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    if not booking_id or booking_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid Booking ID")
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="Database connection missing")
    result = bookings_table.delete_one({"booking_id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"success": True}

@app.get("/products")
def get_products():
    return list(products_table.find({}, {"_id": 0})) if products_table is not None else []

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    if db is None or not product_id or product_id == "undefined":
        return []
    return list(db["reviews"].find({"product_id": product_id}, {"_id": 0}))

@app.post("/reviews")
def add_review(review: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="DB Missing")
    db["reviews"].insert_one(review)
    review.pop("_id", None)
    return review

@app.get("/api/admin/bookings")
@app.get("/bookings")
def get_bookings():
    return list(bookings_table.find({}, {"_id": 0})) if bookings_table is not None else []

@app.post("/api/admin/update-booking")
def update_booking_status(booking_id: str, action: str):
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="DB missing")
    try:
        booking = bookings_table.find_one({"booking_id": booking_id})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        c_name = booking["customer_name"]
        c_phone = booking["customer_phone"]
        p_name = booking["product_name"]

        if action == "agree":
            msg = (
                f"Hello {c_name}! ✅\n\n"
                f"Good news! *{p_name}* is available at Dolphin Trends!\n\n"
                f"🏪 *Plase Visit Our Shop and collect your product:*\n"
                f"Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore\n"
                f"📍 Location Map: https://maps.app.goo.gl/amrkmppGsdgprtx27?g_st=awnn"
                f"⏰ Timings: 11:00 AM - 10:00 PM\n\n"
                f"See you soon! 🛍️\n"
                f"Team Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved"}})
            
        elif action == "disagree":
            msg = (
                f"Hello {c_name},\n\n"
                f"Sorry, *{p_name}* is currently out of stock.\n"
                f"We'll notify you when it's back!\n\n"
                f"Team Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})
            
        elif action == "size_unavail":
            msg = (
                f"Hello {c_name}! 😊\n\n"
                f"*{p_name}* is available but your size is currently out of stock.\n\n"
                f"Please visit our store to check alternatives!\n"
                f"📍 Peenya 2nd Stage, Bangalore\n"
                f"📍 Location Map: https://maps.app.goo.gl/amrkmppGsdgprtx27?g_st=awnn"
                f"Thank you! 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Size Unavailable"}})

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
@app.head("/")
def home():
    return {"status": "Dolphin Trends Cloudinary Secure Backend Active!"}
