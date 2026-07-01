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
import telebot  # 🆕 pyTelegramBotAPI
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton  # 🆕

# 🔄 ಮೀಡಿಯಾ ಗ್ರೂಪ್ ಟ್ರ್ಯಾಕ್
MEDIA_GROUPS = {}

# 🚀 FastAPI Lifespan Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🆕 Bot 1 (Upload) Webhook
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook", timeout=5)
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": f"{BACKEND_URL}/webhook"},
                timeout=5
            )
            print(f"✅ Upload Bot webhook set")
        except Exception as e:
            print(f"Upload Bot webhook error: {e}")
    
    # 🆕 Bot 2 (Chat) Webhook
    if TELEGRAM_CHAT_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_CHAT_BOT_TOKEN}/deleteWebhook", timeout=5)
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_CHAT_BOT_TOKEN}/setWebhook",
                json={"url": f"{BACKEND_URL}/webhook"},
                timeout=5
            )
            print(f"✅ Chat Bot webhook set")
        except Exception as e:
            print(f"Chat Bot webhook error: {e}")
            
    print(f"📸 Upload Bot: {bool(TELEGRAM_BOT_TOKEN)}")
    print(f"💬 Chat Bot: {bool(TELEGRAM_CHAT_BOT_TOKEN)}")
    print(f"👥 Upload Bot Chat ID: {ADMIN_TELEGRAM_CHAT_ID}")
    print(f"👥 Chat Bot Chat ID: {ADMIN_CHAT_BOT_CHAT_ID}")
    print(f"📞 Admin Phones: {ADMIN_PHONES}")
    print(f"📱 WhatsApp Group: {bool(YOUR_WHATSAPP_GROUP_ID)}")
    print(f"📱 WhatsApp Group ID Value: {YOUR_WHATSAPP_GROUP_ID}")
    print(f"☁️ Cloudinary: {bool(CLOUDINARY_CLOUD_NAME)}")
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

# 🆕 Bot 1: Image Upload Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_CHAT_ID = os.getenv("ADMIN_TELEGRAM_CHAT_ID")

# 🆕 Bot 2: Chat Box Bot
TELEGRAM_CHAT_BOT_TOKEN = os.getenv("TELEGRAM_CHAT_BOT_TOKEN")
ADMIN_CHAT_BOT_CHAT_ID = os.getenv("ADMIN_CHAT_BOT_CHAT_ID")

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
chat_messages_table = None

if MONGO_URL:
    try:
        client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
        db = client["dolphin_trends_db"]
        products_table = db["products"]
        bookings_table = db["bookings"]
        chat_messages_table = db["chat_messages"]
        print("✅ MongoDB Connected!")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

# 🛠️ Helper Functions
def upload_to_cloudinary(image_source, is_file=False):
    try:
        if not CLOUDINARY_CLOUD_NAME:
            return None
        result = cloudinary.uploader.upload(
            image_source, folder="dolphin_trends", resource_type="image", timeout=30
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Error: {e}")
        return None

def send_whatsapp_msg(phone, message):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
            return False
        clean_phone = str(phone).strip().replace("+", "").replace(" ", "").replace("-", "")
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
        return response.status_code == 200
    except Exception as e:
        print(f"WhatsApp Error: {e}")
        return False

def send_whatsapp_to_admins(message):
    if not ADMIN_PHONES:
        return []
    results = []
    for idx, phone in enumerate(ADMIN_PHONES, 1):
        results.append(send_whatsapp_msg(phone, message))
        if idx < len(ADMIN_PHONES):
            time.sleep(1)
    return results

# ✅ FIXED: Added full debug logging to see EXACTLY what Green API returns
def send_whatsapp_group_product(image_url):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not YOUR_WHATSAPP_GROUP_ID:
            print(f"⚠️ WA Group SKIPPED - instance:{bool(GREEN_API_INSTANCE)} token:{bool(GREEN_API_TOKEN)} group:{bool(YOUR_WHATSAPP_GROUP_ID)}")
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
        print(f"📤 Sending to WA Group: {YOUR_WHATSAPP_GROUP_ID} | Image: {image_url[:50]}...")
        response = requests.post(url, json=payload, timeout=30)
        print(f"📥 WA Group Response Status: {response.status_code}")
        print(f"📥 WA Group Response Body: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ WA Group EXCEPTION: {type(e).__name__}: {e}")
        return False

# ✅ FIXED: Added debug logging here too
def send_empty_caption_whatsapp_group(image_url):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not YOUR_WHATSAPP_GROUP_ID:
            print(f"⚠️ WA Group (empty caption) SKIPPED - missing config")
            return False
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": YOUR_WHATSAPP_GROUP_ID,
            "urlFile": image_url,
            "fileName": "dolphin_trends.jpg",
            "caption": ""
        }
        response = requests.post(url, json=payload, timeout=30)
        print(f"📥 WA Group (empty caption) Status: {response.status_code} | Body: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ WA Group (empty caption) EXCEPTION: {e}")
        return False

# 🆕 Telegram Helper (pyTelegramBotAPI - Sync)
def send_telegram_with_buttons_upload(chat_id, message, buttons):
    """Upload Bot ಗೆ buttons ಜೊತೆ message"""
    try:
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        keyboard = InlineKeyboardMarkup()
        for btn_row in buttons:
            row_buttons = []
            for btn in btn_row:
                row_buttons.append(InlineKeyboardButton(
                    text=btn["text"],
                    callback_data=btn["data"]
                ))
            keyboard.row(*row_buttons)
        
        bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False


def detect_category_from_name(name):
    if not name:
        return None
    name_lower = name.lower()
    category_map = {
        "formal pant": "Formal Pants", "formal pants": "Formal Pants",
        "formal trouser": "Formal Pants", "formal trousers": "Formal Pants",
        "formal shirt": "Formal Shirt", "formal shirts": "Formal Shirt",
        "office shirt": "Formal Shirt", "office shirts": "Formal Shirt",
        "leggings": "Leggings", "legging": "Leggings",
        "churidar": "Leggings", "churidhar": "Leggings",
        "kurta set": "Kurta Sets", "kurti set": "Kurta Sets",
        "jeans": "Jeans", "jean": "Jeans", "denim": "Jeans",
        "patiala": "Patiala Pants", "patiala pants": "Patiala Pants",
        "kurtha": "Kurtha Top", "kurta top": "Kurtha Top",
        "kurti": "Kurtha Top", "kurtis": "Kurtha Top",
        "umbrella": "Umbrella Sets", "umbrella set": "Umbrella Sets",
        "frock": "Frocks", "frocks": "Frocks", "gown": "Frocks", "gowns": "Frocks",
        "western": "Western Wear", "western wear": "Western Wear",
        "gym": "Gym Pants", "gym pant": "Gym Pants", "gym pants": "Gym Pants",
        "track pant": "Gym Pants", "track pants": "Gym Pants",
        "jogger": "Gym Pants", "joggers": "Gym Pants",
        "250 top": "250 Tops", "250 tops": "250 Tops",
        "350 top": "350 Tops", "350 tops": "350 Tops",
        "jeans top": "Jeans Tops", "jeans tops": "Jeans Tops",
        "top": "Kurtha Top", "tops": "Kurtha Top",
        "t-shirt": "Western Wear", "tshirt": "Western Wear",
        "shirt": "Formal Shirt", "shirts": "Formal Shirt",
        "palazzo": "Plazzo Pants", "plazzo pants": "Plazzo Pants",
        "shrug": "Western Wear", "jacket": "Western Wear", "blazer": "Western Wear",
        "pant": "Formal Pants", "pants": "Formal Pants",
        "trouser": "Formal Pants", "trousers": "Formal Pants",
    }
    sorted_keywords = sorted(category_map.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in name_lower:
            return category_map[keyword]
    return None

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
        "bots": {
            "upload_bot": bool(TELEGRAM_BOT_TOKEN),
            "chat_bot": bool(TELEGRAM_CHAT_BOT_TOKEN)
        },
        "mongo": "connected" if products_table is not None else "not connected",
        "cloudinary": bool(CLOUDINARY_CLOUD_NAME),
        "whatsapp_group_configured": bool(YOUR_WHATSAPP_GROUP_ID),
        "whatsapp_group_id_preview": YOUR_WHATSAPP_GROUP_ID[:15] + "..." if YOUR_WHATSAPP_GROUP_ID else "NOT SET"
    }

@app.head("/")
def home_head():
    return {}

# 🆕 TEST ENDPOINT - directly test WhatsApp group sending
@app.get("/test-wa-group")
def test_wa_group():
    """Test endpoint to directly check WhatsApp group send"""
    test_image = "https://images.unsplash.com/photo-1618932260643-eee4a2f652a6?q=80&w=500"
    result = send_whatsapp_group_product(test_image)
    return {
        "result": result,
        "group_id": YOUR_WHATSAPP_GROUP_ID,
        "instance": GREEN_API_INSTANCE,
        "token_set": bool(GREEN_API_TOKEN)
    }

# 🆕 Chat Box API (Bot 2 - Chat Bot)
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
    """Chat Box using CHAT BOT (Bot 2)"""
    try:
        customer_chat_id = str(uuid.uuid4())[:12]
        
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
        
        if chat_messages_table is not None:
            chat_messages_table.insert_one({
                "customer_chat_id": customer_chat_id,
                "from": "admin",
                "message": welcome_message,
                "timestamp": time.time(),
                "type": "welcome"
            })
            if message:
                chat_messages_table.insert_one({
                    "customer_chat_id": customer_chat_id,
                    "from": "customer",
                    "message": message,
                    "timestamp": time.time(),
                    "type": "customer_message"
                })
        
        bookings_table.insert_one({
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
        })
        
        # ✅ Send to CHAT BOT (Bot 2) with buttons
        if TELEGRAM_CHAT_BOT_TOKEN and ADMIN_CHAT_BOT_CHAT_ID:
            telegram_msg = (
                f"🛍️ <b>New Chat Booking!</b>\n\n"
                f"👤 <b>Customer:</b> {customer_name}\n"
                f"📞 <b>Phone:</b> {customer_phone}\n"
                f"👗 <b>Product:</b> {product_name}\n"
                f"📏 <b>Size:</b> {size}\n"
                f"💰 <b>Price:</b> {price}\n\n"
                f"💬 <b>Message:</b>\n<i>{message or 'No message'}</i>\n\n"
                f"🆔 <b>Chat ID:</b> <code>{customer_chat_id}</code>"
            )
            
            buttons = [
                [
                    {"text": "🟢 Approve", "data": f"approve_{customer_chat_id}"},
                    {"text": "🔴 Disagree", "data": f"reject_{customer_chat_id}"}
                ],
                [
                    {"text": "🟡 Size Unavailable", "data": f"sizeno_{customer_chat_id}"}
                ]
            ]
            
            # Try with image first
            try:
                chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                keyboard = InlineKeyboardMarkup()
                for btn_row in buttons:
                    row_buttons = []
                    for btn in btn_row:
                        row_buttons.append(InlineKeyboardButton(
                            text=btn["text"],
                            callback_data=btn["data"]
                        ))
                    keyboard.row(*row_buttons)
                
                if product_image:
                    try:
                        chat_bot.send_photo(
                            chat_id=ADMIN_CHAT_BOT_CHAT_ID,
                            photo=product_image,
                            caption=telegram_msg,
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                    except:
                        chat_bot.send_message(
                            chat_id=ADMIN_CHAT_BOT_CHAT_ID,
                            text=telegram_msg,
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                else:
                    chat_bot.send_message(
                        chat_id=ADMIN_CHAT_BOT_CHAT_ID,
                        text=telegram_msg,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                print(f"✅ Chat Bot message sent")
            except Exception as e:
                print(f"❌ Chat Bot error: {e}")
        
        # WhatsApp admins
        whatsapp_msg = (
            f"🛍️ *New Chat Booking*\n"
            f"👤 {customer_name}\n"
            f"📞 {customer_phone}\n"
            f"👗 {product_name} (Size: {size})\n"
            f"💰 {price}\n\n"
            f"Check Chat Bot for buttons!"
        )
        send_whatsapp_to_admins(whatsapp_msg)
        
        return {
            "status": "success",
            "customer_chat_id": customer_chat_id,
            "welcome_message": welcome_message
        }
    except Exception as e:
        print(f"❌ Chat Box Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/{customer_chat_id}/messages")
def get_chat_messages(customer_chat_id: str):
    """Polling for live updates"""
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
        return {"status": "error", "messages": []}

# 📋 Bookings API (Existing)
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

# 📦 Products API (Existing)
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
        products_table.insert_one({
            "id": new_id, "product_id": new_id,
            "name": name, "price": price, "original_price": original_price or "",
            "category": category, "description": description or "",
            "image": cloud_image_url, "available": is_available
        })
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

# 🤖 Telegram Webhook - Dual Bot Support
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handles BOTH bots: Upload bot (photos) + Chat bot (callbacks)"""
    try:
        data = await request.json()
        
        # 🆕 Handle Chat Bot callback queries (buttons)
        if "callback_query" in data:
            return await handle_chat_bot_callback(data)
        
        # 📸 Handle Upload Bot photos
        if "message" not in data:
            return {"status": "ok"}

        message = data["message"]
        chat_id = message["chat"]["id"]

        if ALLOWED_USERS and chat_id not in ALLOWED_USERS:
            return {"status": "Ignored"}

        if "photo" not in message:
            return {"status": "ok"}

        # Photo upload logic (existing code)
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
            print(f"🖼️ Single photo - calling send_whatsapp_group_product now...")
            send_whatsapp_group_product(permanent_url)

        # Confirmation (Upload Bot)
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": f"✅ Saved: {product_name} | ₹{product_price.replace('₹','')} | {product_category}"},
            timeout=5
        )

        return {"status": "success"}
    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"status": "error"}


async def handle_chat_bot_callback(data):
    """💬 Chat Bot (Bot 2) button click handler with dynamic button removal and double-click check"""
    try:
        callback = data.get("callback_query")
        callback_data = callback.get("data")
        callback_id = callback.get("id")
        
        # ಬಟನ್ ಇರುವ ಮೆಸೇಜ್ ವಿವರಗಳು (ಟೆಲಿಗ್ರಾಮ್‌ನಲ್ಲಿ ಬಟನ್ ಎಡಿಟ್ ಮಾಡಲು ಬೇಕು)
        message_obj = callback.get("message", {})
        chat_id = message_obj.get("chat", {}).get("id")
        message_id = message_obj.get("message_id")

        print(f"👤 Chat Bot button clicked: {callback_data}")

        # 1. 🛑 CRITICAL CHECK: ಈಗಾಗಲೇ ಒಮ್ಮೆ ಕ್ಲಿಕ್ ಆಗಿದ್ದರೆ, ಮತ್ತೊಮ್ಮೆ ಆಕ್ಷನ್ ರನ್ ಮಾಡಬೇಡಿ
        if callback_data.startswith("clicked_"):
            chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
            chat_bot_instance.answer_callback_query(
                callback_id, 
                text="This action is already processed! ⚠️", 
                show_alert=False
            )
            return {"status": "ok"}

        parts = callback_data.split("_", 1)
        if len(parts) != 2:
            return {"status": "invalid"}

        action, customer_chat_id = parts[0], parts[1]

        booking = bookings_table.find_one({"customer_chat_id": customer_chat_id})
        if not booking:
            chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
            chat_bot_instance.answer_callback_query(callback_id, "❌ Booking not found", show_alert=True)
            return {"status": "not_found"}

        c_name = booking["customer_name"]
        c_phone = booking["customer_phone"]
        p_name = booking["product_name"]

        # 2. ⚡ ಕ್ಲಿಕ್ ಆದ ಆಕ್ಷನ್ ಮೇಲೆ ಸಿಂಗಲ್ ಬಟನ್ ಲೇಔಟ್ ಕ್ರಿಯೇಟ್ ಮಾಡುವುದು
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        updated_keyboard = InlineKeyboardMarkup()

        if action == "approve":
            admin_msg = (
                f"🎉 *Your order has been approved!* ✅\n\n"
                f"Hi {c_name},\n\n"
                f"Great news! Your order for *{p_name}* has been approved! 🎊\n\n"
                f"📍 *Visit our store:*\n"
                f"Rajgopal Nagar Main Road\n"
                f"Peenya 2nd Stage, Bangalore\n\n"
                f"⏰ *Timings:* 11:00 AM - 10:00 PM\n"
                f"📞 *Contact:* 7411255628"
            )
            new_status = "approved"
            whatsapp_msg = (
                f"Hello {c_name}! ✅\n\n"
                f"Good news! *{p_name}* is available at Dolphin Trends!\n\n"
                f"🏪 Rajgopal Nagar Main Road, Peenya 2nd Stage\n"
                f"⏰ 11:00 AM - 10:00 PM"
            )
            response_text = "✅ Order Approved!"
            # ಕೇವಲ Approved ಬಟನ್ ಮಾತ್ರ ಇಡಲಾಗುತ್ತದೆ ಮತ್ತು callback_data ಬದಲಾಯಿಸಲಾಗುತ್ತದೆ
            updated_keyboard.row(InlineKeyboardButton("🟢 Approved", callback_data=f"clicked_approve_{customer_chat_id}"))
            
        elif action == "reject":
            admin_msg = (
                f"😔 *Sorry, Order Unavailable*\n\n"
                f"Hi {c_name},\n\n"
                f"Unfortunately, *{p_name}* is currently out of stock.\n\n"
                f"📦 We'll notify you when it's back!"
            )
            new_status = "rejected"
            whatsapp_msg = f"Sorry, *{p_name}* is currently out of stock."
            response_text = "❌ Order Rejected"
            # ಕೇವಲ Disapproved ಬಟನ್ ಮಾತ್ರ ಇಡಲಾಗುತ್ತದೆ
            updated_keyboard.row(InlineKeyboardButton("🔴 Disapproved", callback_data=f"clicked_reject_{customer_chat_id}"))
            
        elif action == "sizeno":
            admin_msg = (
                f"📏 *Size Not Available*\n\n"
                f"Hi {c_name},\n\n"
                f"*{p_name}* is available, but your size is out of stock.\n\n"
                f"🏪 *Visit our store* to check other available sizes!"
            )
            new_status = "size_no_stock"
            whatsapp_msg = f"*{p_name}* available, but your size sold out."
            response_text = "📏 Size Not Available"
            # ಕೇವಲ Size Unavailable ಬಟನ್ ಮಾತ್ರ ಇಡಲಾಗುತ್ತದೆ
            updated_keyboard.row(InlineKeyboardButton("🟡 Size Unavailable", callback_data=f"clicked_sizeno_{customer_chat_id}"))

        # 3. 🪄 MAGIC: ಟೆಲಿಗ್ರಾಮ್‌ನಲ್ಲಿ ಉಳಿದ ಬಟನ್‌ಗಳನ್ನು ಡಿಲೀಟ್ ಮಾಡಿ ಸಿಂಗಲ್ ಬಟನ್ ಉಳಿಸುವುದು
        chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
        if chat_id and message_id:
            try:
                chat_bot_instance.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=updated_keyboard
                )
            except Exception as keyboard_err:
                print(f"⚠️ Failed to update telegram buttons: {keyboard_err}")

        # 4. 🗄️ Database Updates
        bookings_table.update_one(
            {"customer_chat_id": customer_chat_id},
            {"$set": {"status": new_status, "last_admin_message": admin_msg, "updated_at": time.time()}}
        )
        
        chat_messages_table.insert_one({
            "customer_chat_id": customer_chat_id,
            "from": "admin",
            "message": admin_msg,
            "timestamp": time.time(),
            "type": f"admin_{action}"
        })
        
        # 5. 📱 WhatsApp Notification & Close Telegram Loading Spinner
        send_whatsapp_msg(c_phone, whatsapp_msg)
        chat_bot_instance.answer_callback_query(callback_id, response_text, show_alert=False)
        
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ Callback Error: {e}")
        return {"status": "error"}
