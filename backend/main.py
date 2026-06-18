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
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# 🔄 ಮೀಡಿಯಾ ಗ್ರೂಪ್ ಟ್ರ್ಯಾಕ್
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
            print("Webhook setup error:", e)
            
    print(f"Allowed Telegram Users: {ALLOWED_USERS}")
    print(f"Admin WhatsApp Numbers: {ADMIN_PHONES}")
    print(f"WhatsApp Group ID: {YOUR_WHATSAPP_GROUP_ID}")
    print(f"Telegram Admin Chat ID: {ADMIN_TELEGRAM_CHAT_ID}")
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

# 🌐 Environment Variables
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_CHAT_ID = os.getenv("ADMIN_TELEGRAM_CHAT_ID")  # 🆕 Chat Box ಗಾಗಿ
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
chat_messages_table = None  # 🆕 Chat messages

if MONGO_URL:
    try:
        client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
        db = client["dolphin_trends_db"]
        products_table = db["products"]
        bookings_table = db["bookings"]
        chat_messages_table = db["chat_messages"]  # 🆕
        print("MongoDB Connected Successfully!")
    except Exception as e:
        print(f"MongoDB Connection Error: {e}")

# 🛠️ Helper Functions
def upload_to_cloudinary(image_source, is_file=False):
    try:
        if not CLOUDINARY_CLOUD_NAME:
            return None
        result = cloudinary.uploader.upload(
            image_source,
            folder="dolphin_trends",
            resource_type="image",
            timeout=30
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Error: {str(e)}")
        return None

def send_whatsapp_msg(phone, message):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
            return False
        
        clean_phone = str(phone).strip()
        clean_phone = clean_phone.replace("+", "").replace(" ", "").replace("-", "").strip()
        
        if not clean_phone.isdigit():
            return False
        
        if len(clean_phone) == 10:
            chat_id = f"91{clean_phone}@c.us"
        elif len(clean_phone) == 12 and clean_phone.startswith("91"):
            chat_id = f"{clean_phone}@c.us"
        elif len(clean_phone) >= 10:
            chat_id = f"91{clean_phone[-10:]}@c.us"
        else:
            return False
            
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        response = requests.post(url, json={"chatId": chat_id, "message": message}, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ WhatsApp sent to {phone}")
            return True
        else:
            print(f"❌ WhatsApp failed {phone}: {response.status_code}")
            return False
    except Exception as e:
        print(f"WhatsApp Error ({phone}): {e}")
        return False

def send_whatsapp_to_admins(message):
    if not ADMIN_PHONES:
        return []
    
    results = []
    for idx, phone in enumerate(ADMIN_PHONES, 1):
        success = send_whatsapp_msg(phone, message)
        results.append(success)
        if idx < len(ADMIN_PHONES):
            time.sleep(1)
    
    return results

def send_whatsapp_group_product(image_url):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not YOUR_WHATSAPP_GROUP_ID:
            return False

        caption = (
            "* Offer 🎉*\n"
            "📸 *Follow our Instagram page to get an extra 10% discount*👇\n"
            "🔗 dolphin_trends_rajagopalanagar\n\n"
            "💥 *Explore & order here:* 👇\n"
            "🔗 https://dolphin-trends-two.vercel.app"
        )

        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": YOUR_WHATSAPP_GROUP_ID,
            "urlFile": image_url,
            "fileName": "dolphin_trends_arrival.jpg",
            "caption": caption
        }
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"WhatsApp Group Error: {str(e)}")
        return False

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
        return response.status_code == 200
    except:
        return False

# 🆕 Category Detection
def detect_category_from_name(name):
    if not name:
        return None
    name_lower = name.lower()
    category_map = {
        "formal pant": "Formal Pants", "formal pants": "Formal Pants",
        "formalpant": "Formal Pants", "formalpants": "Formal Pants",
        "formal trouser": "Formal Pants", "formal trousers": "Formal Pants",
        "formal shirt": "Formal Shirt", "formal shirts": "Formal Shirt",
        "formalshirt": "Formal Shirt", "formalshirts": "Formal Shirt",
        "office shirt": "Formal Shirt", "office shirts": "Formal Shirt",
        "leggings": "Leggings", "legging": "Leggings",
        "churidar": "Leggings", "churidhar": "Leggings",
        "kurta set": "Kurta Sets", "kurti set": "Kurta Sets",
        "kurtaset": "Kurta Sets", "kurtiset": "Kurta Sets",
        "jeans": "Jeans", "jean": "Jeans", "denim": "Jeans",
        "patiala": "Patiala Pants", "patiala pants": "Patiala Pants",
        "patiala pant": "Patiala Pants",
        "kurtha": "Kurtha Top", "kurta top": "Kurtha Top",
        "kurti top": "Kurtha Top", "kurti": "Kurtha Top", "kurtis": "Kurtha Top",
        "umbrella": "Umbrella Sets", "umbrella set": "Umbrella Sets",
        "frock": "Frocks", "frocks": "Frocks",
        "frock set": "Frocks", "gown": "Frocks", "gowns": "Frocks",
        "western": "Western Wear", "western wear": "Western Wear",
        "western dress": "Western Wear", "indo western": "Western Wear",
        "indowestern": "Western Wear",
        "gym": "Gym Pants", "gym pant": "Gym Pants", "gym pants": "Gym Pants",
        "track pant": "Gym Pants", "track pants": "Gym Pants",
        "jogger": "Gym Pants", "joggers": "Gym Pants",
        "250 top": "250 Tops", "250 tops": "250 Tops",
        "350 top": "350 Tops", "350 tops": "350 Tops",
        "jeans top": "Jeans Tops", "jeans tops": "Jeans Tops",
        "denim top": "Jeans Tops", "denim tops": "Jeans Tops",
        "top": "Kurtha Top", "tops": "Kurtha Top",
        "t-shirt": "Western Wear", "tshirt": "Western Wear",
        "shirt": "Formal Shirt", "shirts": "Formal Shirt",
        "palazzo": "Plazzo Pants", "plazzo pants": "Plazzo Pants",
        "plazzo pant": "Plazzo Pants",
        "shrug": "Western Wear", "jacket": "Western Wear", "blazer": "Western Wear",
        "pant": "Formal Pants", "pants": "Formal Pants",
        "trouser": "Formal Pants", "trousers": "Formal Pants",
    }
    sorted_keywords = sorted(category_map.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in name_lower:
            return category_map[keyword]
    return None

# 🤖 AI Functions
def _try_google_ai(image_url):
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
            'gemini-1.5-flash-latest', 'gemini-1.5-flash',
            'gemini-1.5-flash-001', 'gemini-1.5-flash-002',
            'gemini-1.5-pro', 'gemini-1.5-pro-001',
            'gemini-pro', 'gemini-pro-vision',
        ]
        prompt = ("Analyze this boutique fashion clothing image. "
                  "1. Simple product name. 2. Category. 3. Short description. "
                  "Format: Name | Category | Description")
        cookie_img = {"mime_type": "image/jpeg", "data": image_bytes}
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                ai_response = model.generate_content([prompt, cookie_img])
                text_res = ai_response.text.strip()
                if "|" in text_res:
                    parts = text_res.split("|")
                    return (parts[0].strip(), parts[1].strip(), parts[2].strip() if len(parts) > 2 else "Beautiful outfit.")
                return "Premium Dress", "Suit Set", "Beautiful design."
            except:
                continue
        return None
    except:
        return None

def _local_fallback_details():
    return "Premium Dress", "Suit Set", "Beautiful design crafted with rich fabric."

def generate_product_details_via_ai(image_url):
    ai_result = _try_google_ai(image_url)
    if ai_result:
        return ai_result
    return _local_fallback_details()

# 🆕 Media Group Processing
async def process_media_group_delayed(media_group_id, delay=3.0):
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
    
    for url in urls[:-1]:
        send_empty_caption_whatsapp_group(url)
        await asyncio.sleep(0.5)
    
    send_whatsapp_group_product(urls[-1])

# 🆕 Chat Box API Endpoints

@app.post("/api/chat-box")
async def chat_box_endpoint(
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    product_name: str = Form("General Inquiry"),
    product_image: str = Form(""),
    size: str = Form("M"),
    price: str = Form("0"),
    message: str = Form(""),
    push_subscription: str = Form(None)
):
    """🆕 Complete chat box workflow"""
    try:
        customer_chat_id = str(uuid.uuid4())[:12]
        
        # ✅ Step 2: Generate welcome message
        welcome_message = (
            f"🎉 *Welcome to Dolphin Trends!* 🐬\n\n"
            f"Hi {customer_name},\n\n"
            f"Thank you for choosing us! We have received your booking request:\n\n"
            f"👗 *{product_name}*\n"
            f"📏 Size: *{size}*\n"
            f"💰 Price: *{price}*\n\n"
            f"📝 *Current Status:* We are checking stock availability. "
            f"Our team will contact you shortly with confirmation. 🙏\n\n"
            f"⏰ You'll get a response within 5 minutes!\n\n"
            f"💥 *Meanwhile, explore our latest collections here:* 👇\n"
            f"🔗 {FRONTEND_URL}\n\n"
            f"✨Thank you for choosing us 😊\n"
            f"*🧑🏻‍💻Team Dolphin Trends* 🐬"
        )
        
        # 💾 Save welcome message
        if chat_messages_table is not None:
            chat_messages_table.insert_one({
                "customer_chat_id": customer_chat_id,
                "from": "admin",
                "message": welcome_message,
                "timestamp": time.time(),
                "type": "welcome"
            })
            
            # Save customer message
            if message:
                chat_messages_table.insert_one({
                    "customer_chat_id": customer_chat_id,
                    "from": "customer",
                    "message": message,
                    "timestamp": time.time(),
                    "type": "customer_message"
                })
        
        # 💾 Save booking
        chat_data = {
            "customer_chat_id": customer_chat_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "product_name": product_name,
            "product_image": product_image,
            "size": size,
            "price": price,
            "message": message,
            "push_subscription": push_subscription,
            "status": "pending",
            "last_admin_message": welcome_message,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        bookings_table.insert_one(chat_data)
        
        # ✅ Step 4: Send to Telegram with 3 buttons
        if TELEGRAM_BOT_TOKEN and ADMIN_TELEGRAM_CHAT_ID:
            telegram_msg = (
                f"🛍️ <b>New Booking Request!</b>\n\n"
                f"👤 <b>Customer:</b> {customer_name}\n"
                f"📞 <b>Phone:</b> {customer_phone}\n"
                f"👗 <b>Product:</b> {product_name}\n"
                f"📏 <b>Size:</b> {size}\n"
                f"💰 <b>Price:</b> {price}\n\n"
                f"💬 <b>Message:</b>\n<i>{message or 'No message'}</i>\n\n"
                f"🆔 <b>Chat ID:</b> <code>{customer_chat_id}</code>"
            )
            
            buttons = [
                [InlineKeyboardButton("🟢 Approve", callback_data=f"approve_{customer_chat_id}"),
                 InlineKeyboardButton("🔴 Disagree", callback_data=f"reject_{customer_chat_id}")],
                [InlineKeyboardButton("🟡 Size Unavailable", callback_data=f"sizeno_{customer_chat_id}")]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            
            try:
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                if product_image:
                    try:
                        await bot.send_photo(
                            chat_id=ADMIN_TELEGRAM_CHAT_ID,
                            photo=product_image,
                            caption=telegram_msg,
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                    except:
                        await bot.send_message(
                            chat_id=ADMIN_TELEGRAM_CHAT_ID,
                            text=telegram_msg,
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                else:
                    await bot.send_message(
                        chat_id=ADMIN_TELEGRAM_CHAT_ID,
                        text=telegram_msg,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                print(f"✅ Telegram message + buttons sent")
            except Exception as e:
                print(f"❌ Telegram error: {e}")
        
        # 📱 Send WhatsApp to admins
        whatsapp_msg = (
            f"🛍️ *New Booking - {customer_name}*\n"
            f"📞 {customer_phone}\n"
            f"👗 {product_name} (Size: {size})\n"
            f"💰 {price}\n\n"
            f"Check Telegram for buttons!"
        )
        send_whatsapp_to_admins(whatsapp_msg)
        
        return {
            "status": "success",
            "customer_chat_id": customer_chat_id,
            "welcome_message": welcome_message,
            "message": "Chat opened! Watch for live updates."
        }
    except Exception as e:
        print(f"❌ Chat Box Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/{customer_chat_id}/messages")
def get_chat_messages(customer_chat_id: str):
    """🔄 Customer polling - live messages"""
    try:
        if chat_messages_table is None:
            return {"status": "error", "messages": []}
        
        messages = list(chat_messages_table.find(
            {"customer_chat_id": customer_chat_id}
        ).sort("timestamp", 1))
        
        booking = bookings_table.find_one({"customer_chat_id": customer_chat_id}) if bookings_table else None
        
        return {
            "status": booking.get("status", "pending") if booking else "unknown",
            "messages": [
                {"from": msg["from"], "message": msg["message"], "timestamp": msg["timestamp"]}
                for msg in messages
            ]
        }
    except Exception as e:
        print(f"❌ Chat polling error: {e}")
        return {"status": "error", "messages": []}


# 📋 Models
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
        "chat_box": "enabled" if ADMIN_TELEGRAM_CHAT_ID else "disabled"
    }

@app.head("/")
def home_head():
    return {}

# 📋 Bookings API
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
            f"✨Thank you for choosing us 😊\n"
            f"*🧑🏻‍💻Team Dolphin Trends* 🐬"
        )
        send_whatsapp_msg(payload.customer_phone, customer_message)

        admin_message = (
            f"🛍️ *New Buy Request Boss😎*\n\n"
            f"👗 *Product:* {payload.product_name}\n"
            f"📏 Size: {payload.size}\n"
            f"💰 Price: {payload.price}\n"
            f"👤 Name: {payload.customer_name}\n"
            f"📞 Phone: {payload.customer_phone}\n\n"
            f"⚙️ *🧑🏻‍💻Plz Update in Admin Panel Boss 👇*\n {FRONTEND_URL}"
        )
        send_whatsapp_to_admins(admin_message)

        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📦 Products API
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

        if file and file.filename:
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
                f"Good news💫 *{p_name}* is available at Dolphin Trends!\n\n"
                f"🛍️ Please visit our shop to collect your product👇\n\n"
                f"🏪 *Store Address:*\n"
                f"Rajgopal Nagar Main Road, Peenya 2nd Stage, Bangalore\n\n"
                f"⏰ Timings: 11:00 AM - 10:00 PM\n\n"
                f"📞 Phone : 9353344035\n\n"
                f"See you soon! 🛍️\n\n 🧑🏻‍💻Team Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved"}})

        elif action == "disagree":
            msg = (
                f"Hello {c_name},\n\n"
                f"Sorry 😔, *{p_name}* is currently out of stock.\n"
                f"We'll notify you when it's back 😇💥\n\n"
                f"✨Thank you for choosing us..🫶\n\n"
                f"🧑🏻‍💻Team Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})

        elif action == "size_unavail" or action == "size_no_stock":
            msg = (
                f"Hello {c_name}! 😊\n\n"
                f"*{p_name}*  is available, but your size is sold out.\n\n"
                f"Drop by our store to check out other sizes 😇\n\n"
                f"🏪Store Address : Rajagopalnagar main road, Peenya 2nd Stage, Bangalore\n\n"
                f"✨Thank you for choosing us..🫶\n\n"
                f"🧑🏻‍💻Team Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Size No Stock"}})

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🤖 Telegram Webhook - WITH Button Handler
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if bookings_table is None:
        return {"status": "DB error"}
    try:
        data = await request.json()
        
        # 🔘 Button Click (Callback Query) - CHAT BOX
        if "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback["data"]
            callback_id = callback["id"]
            
            print(f"🔘 Button clicked: {callback_data}")
            
            parts = callback_data.split("_", 1)
            if len(parts) == 2:
                action, customer_chat_id = parts[0], parts[1]
                
                booking = bookings_table.find_one({"customer_chat_id": customer_chat_id})
                if not booking:
                    return {"status": "not found"}
                
                c_name = booking["customer_name"]
                c_phone = booking["customer_phone"]
                p_name = booking["product_name"]
                
                if action == "approve":
                    admin_msg = (
                        f"🎉 *Your order has been approved!* ✅\n\n"
                        f"Hi {c_name},\n\n"
                        f"Great news! Your order for *{p_name}* has been approved! 🎊\n\n"
                        f"📍 *Visit our store:*\n"
                        f"Rajgopal Nagar Main Road\n"
                        f"Peenya 2nd Stage, Bangalore\n\n"
                        f"⏰ *Timings:* 11:00 AM - 10:00 PM\n"
                        f"📞 *Contact:* 7411255628\n\n"
                        f"Thank you for choosing Dolphin Trends! 🐬"
                    )
                    new_status = "approved"
                    whatsapp_msg = (
                        f"Hello {c_name}! ✅\n\n"
                        f"Good news! *{p_name}* is available!\n\n"
                        f"🏪 Rajgopal Nagar Main Road, Peenya 2nd Stage\n"
                        f"⏰ 11:00 AM - 10:00 PM"
                    )
                    response_text = "✅ Order Approved!"
                    
                elif action == "reject":
                    admin_msg = (
                        f"😔 *Sorry, Order Unavailable*\n\n"
                        f"Hi {c_name},\n\n"
                        f"Unfortunately, *{p_name}* is currently out of stock.\n\n"
                        f"📦 We'll notify you when it's back!\n\n"
                        f"Thank you for choosing us. 🐬"
                    )
                    new_status = "rejected"
                    whatsapp_msg = (
                        f"Hello {c_name},\n\n"
                        f"Sorry, *{p_name}* is currently out of stock.\n"
                        f"We'll notify you when it's back! 💥"
                    )
                    response_text = "❌ Order Rejected"
                    
                elif action == "sizeno":
                    admin_msg = (
                        f"📏 *Size Not Available*\n\n"
                        f"Hi {c_name},\n\n"
                        f"*{p_name}* is available, but your size is currently out of stock.\n\n"
                        f"🏪 *Visit our store* to check other available sizes!\n\n"
                        f"📍 Rajgopal Nagar, Peenya 2nd Stage, Bangalore"
                    )
                    new_status = "size_no_stock"
                    whatsapp_msg = (
                        f"Hello {c_name}! 😊\n\n"
                        f"*{p_name}* is available, but your size is sold out.\n\n"
                        f"Drop by our store to check other sizes!"
                    )
                    response_text = "📏 Size Not Available"
                
                # ✅ Update database
                bookings_table.update_one(
                    {"customer_chat_id": customer_chat_id},
                    {"$set": {
                        "status": new_status,
                        "last_admin_message": admin_msg,
                        "updated_at": time.time()
                    }}
                )
                
                # 💬 Save admin message to chat
                if chat_messages_table is not None:
                    chat_messages_table.insert_one({
                        "customer_chat_id": customer_chat_id,
                        "from": "admin",
                        "message": admin_msg,
                        "timestamp": time.time(),
                        "type": f"admin_{action}"
                    })
                
                # 📱 Send WhatsApp
                send_whatsapp_msg(c_phone, whatsapp_msg)
                
                # ✅ Answer callback
                try:
                    bot = Bot(token=TELEGRAM_BOT_TOKEN)
                    await bot.answer_callback_query(
                        callback_query_id=callback_id,
                        text=response_text,
                        show_alert=False
                    )
                except:
                    pass
            
            return {"status": "ok"}
        
        # Regular message handler (photo upload)
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

        if caption:
            has_valid_caption = True
            clean_caption = caption.replace("#edit", "").strip()
            lines = [l.strip() for l in clean_caption.split("\n") if l.strip()]
            clean_text = " ".join(lines)
            price_match = re.search(r'(?:Rs\.?\s*|₹\s*)?(\d{3,5})', clean_text)

            if "-" in clean_caption:
                parts = clean_caption.split("-")
                if len(parts) >= 3:
                    product_name = parts[0].strip()
                    product_price = parts[1].strip()
                    product_category = parts[2].strip()
                    if len(parts) >= 4:
                        product_description = parts[3].strip()
            elif price_match:
                product_price = price_match.group(1)
                remaining_text = clean_text.replace(price_match.group(0), "").replace("₹", "").replace("Rs", "").replace("rs", "").strip()
                if remaining_text and len(remaining_text) > 2:
                    product_name = remaining_text
                    detected_cat = detect_category_from_name(product_name)
                    if detected_cat:
                        product_category = detected_cat
            else:
                product_name = clean_text
                detected_cat = detect_category_from_name(product_name)
                if detected_cat:
                    product_category = detected_cat

        if media_group_id:
            if media_group_id not in MEDIA_GROUPS:
                MEDIA_GROUPS[media_group_id] = {
                    "name": product_name, "price": product_price,
                    "category": product_category, "description": product_description,
                    "user_caption": caption, "processed_urls": [], "task": None
                }
            if caption:
                MEDIA_GROUPS[media_group_id].update({
                    "name": product_name, "price": product_price,
                    "category": product_category, "description": product_description,
                    "user_caption": caption
                })

        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
            params={"file_id": file_id}, timeout=10
        ).json()
        file_path = file_info.get("result", {}).get("file_path")

        if not file_path:
            return {"status": "ok"}

        telegram_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        permanent_url = upload_to_cloudinary(telegram_image_url)
        if not permanent_url:
            permanent_url = telegram_image_url

        if not has_valid_caption:
            ai_name, ai_cat, ai_desc = generate_product_details_via_ai(permanent_url)
            product_name = ai_name
            product_category = ai_cat
            product_description = ai_desc

        product_price_display = product_price if product_price.startswith("₹") else f"₹{product_price}"

        if media_group_id and media_group_id in MEDIA_GROUPS:
            group_data = MEDIA_GROUPS[media_group_id]
            product_name = group_data["name"]
            product_price = group_data["price"]
            product_category = group_data["category"]
            product_description = group_data["description"]
            product_price_display = product_price if product_price.startswith("₹") else f"₹{product_price}"
            group_data["processed_urls"].append(permanent_url)

        new_id = str(uuid.uuid4())[:8]
        products_table.insert_one({
            "product_id": new_id, "id": new_id,
            "name": product_name, "price": product_price_display,
            "category": product_category, "image": permanent_url,
            "description": product_description, "available": True
        })

        if media_group_id:
            old_task = MEDIA_GROUPS[media_group_id].get("task")
            if old_task and not old_task.done():
                old_task.cancel()
            MEDIA_GROUPS[media_group_id]["task"] = asyncio.create_task(
                process_media_group_delayed(media_group_id, delay=3.0)
            )
        else:
            send_whatsapp_group_product(permanent_url)

        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": f"✅ Saved: {product_name}"},
            timeout=5
        )

        return {"status": "success"}
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return {"status": "error"}
