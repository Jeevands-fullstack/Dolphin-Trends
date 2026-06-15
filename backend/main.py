import os
import io
import uuid
import time
import asyncio
import requests
import re
import random
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
import cloudinary
import cloudinary.uploader

# 🔄 ಮೀಡಿಯಾ ಗ್ರೂಪ್‌ಗಳನ್ನು ಪಕ್ಕಾ ಆಗಿ ಟ್ರ್ಯಾಕ್ ಮಾಡಲು ಗ್ಲೋಬಲ್ ಮೆಮೊರಿ
MEDIA_GROUPS = {}

# 🚀 FastAPI Lifespan Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook", timeout=5)
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": f"{BACKEND_URL}/webhook"},
                timeout=5
            )
            print("Webhook set successfully:", r.text)
        except Exception as e:
            print("Webhook setup error during startup:", e)
            
    print(f"Allowed Telegram Users: {ALLOWED_USERS}")
    print(f"Admin WhatsApp Numbers: {ADMIN_PHONES}")
    print(f"WhatsApp Group ID: {YOUR_WHATSAPP_GROUP_ID}")
    print(f"Cloudinary configured: {bool(CLOUDINARY_CLOUD_NAME)}")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🌐 Environment Variables Configuration
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "https://dolphin-trends-3.onrender.com"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"
INSTAGRAM_URL = "https://www.instagram.com/dolphin_trends_rajagopalanagar?igsh=MWJ4MGRybGFxOXdiYw=="

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY_VAL = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY_VAL,
    api_secret=CLOUDINARY_API_SECRET
)

YOUR_PERSONAL_PHONE = "917411255628"
SECOND_PERSONAL_PHONE = os.getenv("SECOND_PERSONAL_PHONE", "")
THIRD_PERSONAL_PHONE = os.getenv("THIRD_PERSONAL_PHONE", "")
ADMIN_PHONES = [p for p in [YOUR_PERSONAL_PHONE, SECOND_PERSONAL_PHONE, THIRD_PERSONAL_PHONE] if p]

YOUR_WHATSAPP_GROUP_ID = os.getenv("YOUR_WHATSAPP_GROUP_ID", "")

ALLOWED_USERS_STR = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = [int(x.strip()) for x in ALLOWED_USERS_STR.split(",") if x.strip().lstrip("-").isdigit()]
single_chat_id = os.getenv("chat_id", "")
if single_chat_id.strip().lstrip("-").isdigit():
    ALLOWED_USERS.append(int(single_chat_id.strip()))

ca = certifi.where()
db = None
bookings_table = None
products_table = None

if MONGO_URL:
    try:
        client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
        db = client["dolphin_trends_db"]
        products_table = db["products"]
        bookings_table = db["bookings"]
        print("MongoDB Connected Successfully!")
    except Exception as e:
        print(f"MongoDB Connection Error: {e}")

# 🛠️ Helper Functions
def upload_to_cloudinary(image_source, is_file=False):
    try:
        if not CLOUDINARY_CLOUD_NAME:
            print("Cloudinary not configured!")
            return None
        result = cloudinary.uploader.upload(
            image_source,
            folder="dolphin_trends",
            resource_type="image",
            timeout=30
        )
        url = result.get("secure_url")
        print(f"Cloudinary upload success: {url}")
        return url
    except Exception as e:
        print(f"Cloudinary Upload Error: {str(e)}")
        return None

def send_whatsapp_msg(phone, message):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
            return False
        clean_phone = str(phone).replace("+", "").replace(" ", "").replace("-", "").strip()
        if len(clean_phone) >= 10:
            just_10_digits = clean_phone[-10:]
            chat_id = f"91{just_10_digits}@c.us"
        else:
            print(f"❌ Invalid Phone Number length: {clean_phone}")
            return False
            
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        response = requests.post(url, json={"chatId": chat_id, "message": message}, timeout=10)
        print(f"WhatsApp Sent to {chat_id}, Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"WhatsApp Msg Error ({phone}): {e}")
        return False

def send_whatsapp_to_admins(message):
    for phone in ADMIN_PHONES:
        send_whatsapp_msg(phone, message)

# 📸 ವಾಟ್ಸಾಪ್ ಗ್ರೂಪ್‌ಗೆ ಆಫರ್ ಲಿಂಕ್ ಕಳಿಸುವ ಫಂಕ್ಷನ್ (ಕೇವಲ ಕೊನೆ ಫೋಟೋಗೆ ಮಾತ್ರ)
def send_whatsapp_group_product(image_url, user_caption=None):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not YOUR_WHATSAPP_GROUP_ID:
            print("WhatsApp group not configured")
            return False

        links_text = (
            f"📸 *If you follow our instagram page and get extra 10% discount:* 👇\n"
            f"🔗 {INSTAGRAM_URL}\n\n"
            f"💥 *Explore & order here:* 👇\n"
            f"🔗 {FRONTEND_URL}"
        )
        
        caption = f"{user_caption}\n\n{links_text}".strip() if user_caption else links_text

        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": YOUR_WHATSAPP_GROUP_ID,
            "urlFile": image_url,
            "fileName": "dolphin_trends_arrival.jpg",
            "caption": caption
        }
        response = requests.post(url, json=payload, timeout=30)
        print("WhatsApp Group Status (With Links):", response.status_code)
        return response.status_code == 200
    except Exception as e:
        print("WhatsApp Group Error:", str(e))
        return False

# 🖼️ ಮಧ್ಯದ ಫೋಟೋಗಳಿಗೆ ಬರೀ ಇಮೇಜ್ ಮಾತ್ರ ಕಳಿಸುವ ಫಂಕ್ಷನ್
def send_empty_caption_whatsapp_group(image_url):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not YOUR_WHATSAPP_GROUP_ID:
            return False
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": YOUR_WHATSAPP_GROUP_ID,
            "urlFile": image_url,
            "fileName": "dolphin_trends.jpg",
            "caption": ""
        }
        response = requests.post(url, json=payload, timeout=30)
        print("WhatsApp Group Status (Empty Caption):", response.status_code)
        return True
    except Exception as e:
        print("Error sending empty caption image:", e)
        return False

# 🆕 Smart Category Detection - ನಿಮ್ಮ website categories ಗೆ match ಮಾಡಿ
def detect_category_from_name(name):
    """Name ನಲ್ಲಿ ಯಾವ category keyword ಇದೆ ಎಂದು ಪತ್ತೆ ಮಾಡಿ - ನಿಮ್ಮ website categories ಗೆ"""
    if not name:
        return None
    
    name_lower = name.lower()
    
    # ✅ ನಿಮ್ಮ website ನ ಎಲ್ಲಾ categories
    category_map = {
        # Leggings
        "leggings": "Leggings",
        "legging": "Leggings",
        "leggins": "Leggings",
        "leggins": "Leggings",
        
        # Kurta Sets
        "kurta set": "Kurta Sets",
        "kurti set": "Kurta Sets",
        "kurtaset": "Kurta Sets",
        "kurtiset": "Kurta Sets",
        
        # Jeans
        "jeans": "Jeans",
        "jean": "Jeans",
        "jeans": "Jeans",
        
        # Patiala Pants
        "plazzo Pants": "Patiala Pants",
        "plazzo pants": "Plazzo Pants",
        "plazzo pant": "Plazzo Pants",
        
        # Kurtha Top
        "kurtha": "Kurtha Top",
        "kurta top": "Kurtha Top",
        "kurti top": "Kurtha Top",
        "kurti": "Kurtha Top",
        "kurtis": "Kurtha Top",
        
        # Umbrella Sets
        "umbrella": "Umbrella Sets",
        "umbrella set": "Umbrella Sets",
        
        # Frocks
        "frock": "Frocks",
        "frocks": "Frocks",
        "frock set": "Frocks",
        "gown": "Frocks",
        "gowns": "Frocks",
        
        # Western Wear
        "western": "Western Wear",
        "western wear": "Western Wear",
        "western dress": "Western Wear",
        "indo western": "Western Wear",
        "indowestern": "Western Wear",
        
        # Gym Pants
        "gym": "Gym Pants",
        "gym pant": "Gym Pants",
        "gym pants": "Gym Pants",
        "track pant": "Gym Pants",
        "track pants": "Gym Pants",
        "jogger": "Gym Pants",
        "joggers": "Gym Pants",
        
        # 250 Tops
        "250 top": "250 Tops",
        "250 tops": "250 Tops",
        
        # 350 Tops
        "350 top": "350 Tops",
        "350 tops": "350 Tops",
        
        # Jeans Tops
        "jeans top": "Jeans Tops",
        "jeans tops": "Jeans Tops",
        "denim top": "Jeans Tops",
        "denim tops": "Jeans Tops",
        
        # ಬೇರೆ common words
        "top": "Kurtha Top",
        "tops": "Kurtha Top",
        "t-shirt": "Western Wear",
        "tshirt": "Western Wear",
        "shirt": "Western Wear",
        "shirts": "Western Wear",
        "palazzo": "Patiala Pants",
        "shrug": "Western Wear",
        "jacket": "Western Wear",
        "blazer": "Western Wear",
    }
    
    # Sort by length (longest first)
    sorted_keywords = sorted(category_map.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in name_lower:
            return category_map[keyword]
    
    return None

# 🤖 Google AI Function - Try Multiple Models
def _try_google_ai(image_url):
    """Google AI try ಮಾಡುತ್ತದೆ, None ಅಥವಾ result return ಮಾಡುತ್ತದೆ"""
    try:
        if not GOOGLE_API_KEY:
            return None
        
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        
        response = requests.get(image_url, timeout=10)
        image_bytes = response.content
        
        if not image_bytes:
            return None
        
        model_names = [
            'gemini-1.5-flash',
            'gemini-1.5-flash-001',
            'gemini-1.5-flash-002',
            'gemini-1.5-pro',
            'gemini-1.5-pro-001',
            'gemini-pro',
            'gemini-pro-vision',
        ]
        
        prompt = (
            "Analyze this boutique fashion clothing image. "
            "1. Provide a simple product name. "
            "2. Category (one or two words). "
            "3. Short attractive description (1-2 sentences). "
            "Format: Name | Category | Description"
        )
        cookie_img = {"mime_type": "image/jpeg", "data": image_bytes}
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                ai_response = model.generate_content([prompt, cookie_img])
                text_res = ai_response.text.strip()
                print(f"✅ AI Success with {model_name}")
                
                if "|" in text_res:
                    parts = text_res.split("|")
                    return (
                        parts[0].strip(),
                        parts[1].strip(),
                        parts[2].strip() if len(parts) > 2 else "Beautiful outfit."
                    )
                return "Premium Dress", "Suit Set", "Beautiful design crafted with rich fabric."
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"⚠️ Quota exceeded for {model_name}")
                elif "404" in error_msg:
                    print(f"⚠️ Model {model_name} not found")
                else:
                    print(f"❌ Model {model_name} error: {error_msg[:100]}")
                continue
        
        return None
    except:
        return None

# 🆕 Local Fallback
def _local_fallback_details():
    """AI work ಆಗದಿದ್ದರೆ default values"""
    return "Premium Dress", "Suit Set", "Beautiful design crafted with rich fabric."

# 🤖 Main AI Function
def generate_product_details_via_ai(image_url):
    """AI try ಮಾಡುತ್ತದೆ, fail ಆದರೆ local fallback ಬಳಸುತ್ತದೆ"""
    ai_result = _try_google_ai(image_url)
    if ai_result:
        return ai_result
    
    print("⚠️ Using local fallback")
    return _local_fallback_details()

# 🆕 Async helper: Media group delay processing
async def process_media_group_delayed(media_group_id, delay=3.0):
    """ಎಲ್ಲಾ photos ಬರುವವರೆಗೆ wait ಮಾಡಿ, ಆಮೇಲೆ WhatsApp ಗೆ ಕಳುಹಿಸಿ"""
    try:
        await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return
    
    if media_group_id not in MEDIA_GROUPS:
        return
    
    group_data = MEDIA_GROUPS.pop(media_group_id, None)
    if not group_data:
        return
    
    urls = group_data.get("processed_urls", [])
    if not urls:
        return
    
    print(f"📤 Processing media group {media_group_id} with {len(urls)} images")
    
    # 📸 ಮೊದಲ N-1 photos: ಬರೀ image (link ಇಲ್ಲ)
    for url in urls[:-1]:
        send_empty_caption_whatsapp_group(url)
        await asyncio.sleep(0.5)
    
    # 🎯 ಕೊನೆಯ photo: link ಜೊತೆ
    last_url = urls[-1]
    user_text = group_data.get("user_caption", "")
    send_whatsapp_group_product(last_url, user_caption=user_text)
    print(f"✅ Media group processed successfully!")

class BookingPayload(BaseModel):
    customer_name: str
    customer_phone: str
    product_name: str
    image_url: str
    size: str = "M"
    price: str = "1299"

@app.get("/")
def home():
    return {
        "status": "Dolphin Trends Backend Active!",
        "mongo": "connected" if products_table is not None else "not connected",
        "cloudinary": "configured" if CLOUDINARY_CLOUD_NAME else "missing"
    }

@app.head("/")
def home_head():
    return {}

# 🔍 Available AI models endpoint
@app.get("/api/list-models")
def list_available_models():
    """Google API ನಲ್ಲಿ ಯಾವ models ಲಭ್ಯ ಎಂದು ತೋರಿಸುತ್ತದೆ"""
    try:
        if not GOOGLE_API_KEY:
            return {"error": "GOOGLE_API_KEY missing"}
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        
        models = genai.list_models()
        available = []
        for m in models:
            methods = list(m.supported_generation_methods) if hasattr(m, 'supported_generation_methods') else []
            if 'generateContent' in methods:
                available.append(m.name)
        return {"available_models": available, "count": len(available)}
    except Exception as e:
        return {"error": str(e)}

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
            f"Thank you for choosing us! 😊\n"
            f"*Team Dolphin Trends* 🐬"
        )
        send_whatsapp_msg(payload.customer_phone, customer_message)

        admin_message = (
            f"🛍️ *New Buy Request Boss!*\n\n"
            f"👗 *Product:* {payload.product_name}\n"
            f"📏 Size: {payload.size}\n"
            f"💰 Price: {payload.price}\n"
            f"👤 Name: {payload.customer_name}\n"
            f"📞 Phone: {payload.customer_phone}\n\n"
            f"⚙️ *Plz update in Admin Panel Boss:* {FRONTEND_URL}"
        )
        send_whatsapp_to_admins(admin_message)

        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products")
async def add_product(
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
        cloud_image_url = None

        if file and file.filename and file.filename != "":
            file_bytes = await file.read()
            if file_bytes and len(file_bytes) > 100:
                cloud_image_url = upload_to_cloudinary(file_bytes, is_file=True)
                if not cloud_image_url:
                    raise HTTPException(status_code=500, detail="Image upload failed!")
            else:
                raise HTTPException(status_code=400, detail="Empty file!")
        else:
            raise HTTPException(status_code=400, detail="Please upload a product image!")

        new_id = str(uuid.uuid4())[:8]
        product_data = {
            "id": new_id, "product_id": new_id,
            "name": name, "price": price, "original_price": original_price or "",
            "category": category, "description": description or "",
            "image": cloud_image_url, "available": is_available
        }
        products_table.insert_one(product_data)

        send_whatsapp_group_product(cloud_image_url, f"👗 *{name}* - {price}")

        return {"status": "success", "action": "created", "product_id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/products/{product_id}")
@app.put("/products/{product_id}")
def update_product(product_id: str, payload: dict):
    if products_table is None:
        raise HTTPException(status_code=500, detail="DB missing")
    products_table.update_one(
        {"$or": [{"product_id": product_id}, {"id": product_id}]},
        {"$set": payload}
    )
    return {"status": "success"}

@app.delete("/api/products/{product_id}")
@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    if products_table is None:
        raise HTTPException(status_code=500, detail="DB missing")
    products_table.delete_one({"$or": [{"product_id": product_id}, {"id": product_id}]})
    return {"success": True}

@app.get("/products")
def get_products():
    if products_table is None:
        return []
    return list(products_table.find({}, {"_id": 0}))

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    if db is None:
        return []
    return list(db["reviews"].find({"product_id": product_id}, {"_id": 0}))

@app.post("/reviews")
def add_review(review: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="DB missing")
    review["id"] = str(uuid.uuid4())
    db["reviews"].insert_one(review)
    review.pop("_id", None)
    return review

@app.get("/api/admin/bookings")
@app.get("/bookings")
def get_bookings():
    if bookings_table is None:
        return []
    return list(bookings_table.find({}, {"_id": 0}))

@app.delete("/api/admin/bookings/{booking_id}")
@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="DB missing")
    bookings_table.delete_one({"booking_id": booking_id})
    return {"success": True}

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
                f"Good news! *{p_name}* is available at Dolphin Trends🐬 plz visit our shop and collect your product 🛍️!\n\n"
                f"🏪 *Store Address:*\n"
                f"Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore\n"
                f"📍 Map: https://maps.google.com\n"
                f"⏰ Timings: 11:00 AM - 10:00 PM\n\n"
                f"See you soon! 🛍️\nTeam Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved"}})

        elif action == "disagree":
            msg = (
                f"Hello {c_name},\n\n"
                f"Sorry, *{p_name}* is currently out of stock.\n"
                f"We'll notify you when it's back! 💥\n\nTeam Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🤖 💥 ಪಕ್ಕಾ ಮಾಸ್ಟರ್ ವೆಬ್‌ಹುಕ್
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if products_table is None:
        return {"status": "DB error"}
    try:
        data = await request.json()
        if "message" not in data:
            return {"status": "ok"}

        message = data["message"]
        chat_id = message["chat"]["id"]

        if ALLOWED_USERS and chat_id not in ALLOWED_USERS:
            return {"status": "Ignored"}

        if "photo" not in message:
            return {"status": "ok"}

        caption = message.get("caption", "").strip()
        media_group_id = message.get("media_group_id")
        
        product_name = "Premium Dress"
        product_price = "1500"
        product_category = "Suit Set"
        product_description = "Curated boutique wear."
        has_valid_caption = False

        # ✅ ಟೆಕ್ಸ್ಟ್ ಪಾರ್ಸಿಂಗ್ - ನಿಮ್ಮ website categories ಗೆ match
        if caption:
            has_valid_caption = True
            clean_caption = caption.replace("#edit", "").strip()
            lines = [l.strip() for l in clean_caption.split("\n") if l.strip()]
            clean_text = " ".join(lines)
            price_match = re.search(r'(?:Rs\.?\s*|₹\s*)?(\d{3,5})', clean_text)

            if "-" in clean_caption:
                # Format: "Name - Price - Category"
                parts = clean_caption.split("-")
                if len(parts) >= 3:
                    product_name = parts[0].strip()
                    product_price = parts[1].strip()
                    product_category = parts[2].strip()
                    if len(parts) >= 4:
                        product_description = parts[3].strip()
            elif price_match:
                product_price = price_match.group(1)
                # ✅ ಬರೀ price ಅಥವಾ price + name handle ಮಾಡಿ
                remaining_text = clean_text.replace(price_match.group(0), "").replace("₹", "").replace("Rs", "").replace("rs", "").strip()
                if remaining_text and len(remaining_text) > 2:
                    product_name = remaining_text
                    # ✅ Name ನಿಂದ category auto-detect
                    detected_cat = detect_category_from_name(product_name)
                    if detected_cat:
                        product_category = detected_cat
                        print(f"✅ Auto-detected: {detected_cat} from {product_name}")
                # ಬರೀ price ಮಾತ್ರ ಇದ್ದರೆ default ("Premium Dress" + "Suit Set") ಉಳಿಯುತ್ತದೆ
            else:
                # ✅ ಬರೀ name ಇದೆ (price ಇಲ್ಲ, dash ಇಲ್ಲ)
                product_name = clean_text
                detected_cat = detect_category_from_name(product_name)
                if detected_cat:
                    product_category = detected_cat
                    print(f"✅ Auto-detected: {detected_cat} from {product_name}")
                # Category detect ಆಗಲಿಲ್ಲ ಎಂದಾದರೆ default ("Suit Set") ಉಳಿಯುತ್ತದೆ

        # ಫೋಟೋ ಡೌನ್‌ಲೋಡ್ ಲಾಜಿಕ್
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=10
        ).json()
        file_path = file_info.get("result", {}).get("file_path")

        if not file_path:
            return {"status": "ok"}

        telegram_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        permanent_url = upload_to_cloudinary(telegram_image_url)
        if not permanent_url:
            permanent_url = telegram_image_url

        # AI ಅಥವಾ Fallback
        if not has_valid_caption:
            ai_name, ai_cat, ai_desc = generate_product_details_via_ai(permanent_url)
            product_name = ai_name
            product_category = ai_cat
            product_description = ai_desc

        product_price_display = product_price if product_price.startswith("₹") else f"₹{product_price}"

        # ವೆಬ್‌ಸೈಟ್ ಡೇಟಾಬೇಸ್‌ಗೆ ಸೇವ್
        new_id = str(uuid.uuid4())[:8]
        products_table.insert_one({
            "product_id": new_id, "id": new_id,
            "name": product_name, "price": product_price_display,
            "category": product_category, "image": permanent_url,
            "description": product_description, "available": True
        })

        # 🔥 ವಾಟ್ಸಾಪ್ ಗ್ರೂಪ್ ಸ್ಮಾರ್ಟ್ ಫಿಲ್ಟರಿಂಗ್ ಲಾಜಿಕ್ (Async Non-Blocking) 🔥
        if media_group_id:
            # Group data initialize/update ಮಾಡಿ
            if media_group_id not in MEDIA_GROUPS:
                MEDIA_GROUPS[media_group_id] = {
                    "name": product_name,
                    "price": product_price,
                    "category": product_category,
                    "description": product_description,
                    "user_caption": caption,
                    "processed_urls": [],
                    "task": None
                }
            
            # URL add ಮಾಡಿ
            MEDIA_GROUPS[media_group_id]["processed_urls"].append(permanent_url)
            
            # ಹೊಸ caption ಬಂದರೆ update ಮಾಡಿ
            if caption:
                MEDIA_GROUPS[media_group_id]["user_caption"] = caption
                MEDIA_GROUPS[media_group_id]["name"] = product_name
                MEDIA_GROUPS[media_group_id]["price"] = product_price
                MEDIA_GROUPS[media_group_id]["category"] = product_category
                MEDIA_GROUPS[media_group_id]["description"] = product_description
            
            # ❌ ಹಳೆ task cancel ಮಾಡಿ
            old_task = MEDIA_GROUPS[media_group_id].get("task")
            if old_task and not old_task.done():
                old_task.cancel()
            
            # ✅ ಹೊಸ async task ಶುರು ಮಾಡಿ (3 sec ನಂತರ process)
            MEDIA_GROUPS[media_group_id]["task"] = asyncio.create_task(
                process_media_group_delayed(media_group_id, delay=3.0)
            )
        else:
            # ಒಂದೇ ಒಂದು photo: ನೇರವಾಗಿ link ಜೊತೆ ಕಳುಹಿಸಿ
            send_whatsapp_group_product(permanent_url, user_caption=caption if caption else None)

        # ಟೆಲಿಗ್ರಾಮ್ ಕನ್ಫರ್ಮೇಷನ್
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": f"✅ Saved: {product_name} | Category: {product_category}"},
            timeout=5
        )

        return {"status": "success"}
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return {"status": "error"}
