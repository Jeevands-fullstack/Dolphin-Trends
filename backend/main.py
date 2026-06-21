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
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🎬 ಮೀಡಿಯಾ ಗ್ರೂಪ್ಸ್ ಮ್ಯಾಪ್
MEDIA_GROUPS = {}

# 🆕 Rate limiting for admin actions
last_admin_action = {}

def check_rate_limit(chat_id, action_type, cooldown_seconds=10):
    """Prevent spam from same admin"""
    key = f"{chat_id}_{action_type}"
    now = time.time()
    
    if key in last_admin_action:
        if now - last_admin_action[key] < cooldown_seconds:
            return False
    
    last_admin_action[key] = now
    return True

# 🚀 FastAPI Lifespan Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🤖 Bot 1 (Upload) Webhook
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
            print(f"❌ Upload Bot webhook error: {e}")

    # 🤖 Bot 2 (Chat) Webhook
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
            print(f"❌ Chat Bot webhook error: {e}")

    print(f"🤖 Upload Bot: {bool(TELEGRAM_BOT_TOKEN)}")
    print(f"💬 Chat Bot: {bool(TELEGRAM_CHAT_BOT_TOKEN)}")
    print(f"📢 Upload Chat ID: {bool(ADMIN_TELEGRAM_CHAT_ID)}")
    print(f"👥 Chat Bot Chat ID: {bool(ADMIN_CHAT_BOT_CHAT_ID)}")
    print(f"📞 Admin Phones: {ADMIN_PHONES}")
    print(f"💬 WhatsApp Group: {bool(YOUR_WHATSAPP_GROUP_ID)}")
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

# 🤖 Bot 1: Image Upload Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_CHAT_ID = os.getenv("ADMIN_TELEGRAM_CHAT_ID")

# 🤖 Bot 2: Chat Box Bot
TELEGRAM_CHAT_BOT_TOKEN = os.getenv("TELEGRAM_CHAT_BOT_TOKEN")
ADMIN_CHAT_BOT_CHAT_ID = os.getenv("ADMIN_CHAT_BOT_CHAT_ID")

BACKEND_URL = "https://dolphin-trends-3.onrender.com"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"
INSTAGRAM_URL = "https://www.instagram.com/dolphin_trends_rajagopalanagar?igsh=MWJ4MGRybGFxdXdlYw=="

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY_VAL = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY_VAL,
    api_secret=CLOUDINARY_API_SECRET
)

YOUR_PERSONAL_PHONE = "917411255620"
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
        print(f" Cloudinary Error: {e}")
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
        elif len(clean_phone) > 10:
            chat_id = f"{clean_phone[-10:]}@c.us"
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

def send_whatsapp_group_product(image_url):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not YOUR_WHATSAPP_GROUP_ID:
            return False
        caption = (
            "*✨ New Arrival Alert! ✨*\n\n"
            "🎁 *Offer:* 🔥\n"
            "📸 *Follow our Instagram page to get an extra 10% discount* 👇\n"
            "🔗 https://www.instagram.com/dolphin_trends_rajagopalanagar/\n\n"
            "✨ *Explore & order here:* ✨\n"
            f"🔗 {FRONTEND_URL}"
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
    except Exception:
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
    except Exception:
        return False

def send_telegram_with_buttons_upload(chat_id, message, buttons):
    try:
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        keyboard = InlineKeyboardMarkup()
        for btn_row in buttons:
            row_buttons = []
            for btn in btn_row:
                row_buttons.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["data"]))
            keyboard.row(*row_buttons)
        bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard, parse_mode="HTML")
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
        "jagger": "Gym Pants", "jeggers": "Gym Pants",
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
            'gemini-pro', 'gemini-pro-vision'
        ]
        prompt = "Analyze this boutique fashion clothing image. Format: Name | Category | Description"
        cookie_img = {"mime_type": "image/jpeg", "data": image_bytes}
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                ai_response = model.generate_content([prompt, cookie_img])
                text_res = ai_response.text.strip()
                if "|" in text_res:
                    parts = text_res.split("|")
                    return parts[0].strip(), parts[1].strip(), parts[2].strip()
            except Exception:
                continue
        return None
    except Exception:
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
        "cloudinary": bool(CLOUDINARY_CLOUD_NAME)
    }

@app.head("/")
def home_head():
    return {}

# 🆕 Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "mongo": "connected" if products_table is not None else "disconnected",
        "bots": {
            "upload": bool(TELEGRAM_BOT_TOKEN),
            "chat": bool(TELEGRAM_CHAT_BOT_TOKEN)
        },
        "timestamp": time.time()
    }

# ============================================================
# 💬 CHAT BOX SYSTEM (Bot 2 - Chat Bot) - NEW LIVE CHAT FEATURES
# ============================================================

@app.post("/api-chat-box")
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
    try:
        customer_chat_id = str(uuid.uuid4())[:12]
        
        # ✅ FIXED: Bold formatting with asterisks
        welcome_message = (
            f"👋 *Welcome to Dolphin Trends!* 🐬\n\n"
            f"Hi *{customer_name}*,\n"
            f"Thank you for choosing us! We have received your booking request:\n\n"
            f"👗 *{product_name}*\n"
            f"📏 Size: *{size}*\n"
            f"💰 Price: *₹{price}*\n\n"
            f"⏳ Current Status: We are checking stock availability.\n"
            f"Our team will contact you shortly with confirmation. 🙏\n\n"
            f"👋 Thank you for choosing us 😊\n"
            f"🏢 *Team Dolphin Trends* 🐬"
        )
        
        if chat_messages_table is not None:
            chat_messages_table.insert_one({
                "customer_chat_id": customer_chat_id,
                "from": "admin",
                "message": welcome_message,
                "timestamp": time.time(),
                "type": "welcome",
                "read": False
            })
            
            if message:
                chat_messages_table.insert_one({
                    "customer_chat_id": customer_chat_id,
                    "from": "customer",
                    "message": message,
                    "timestamp": time.time() + 0.1,
                    "type": "customer_message",
                    "read": False
                })
            
        if bookings_table is not None:
            bookings_table.insert_one({
                "booking_id": customer_chat_id,
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
            
        # ✅ IMPROVED: Better formatted Telegram message
        if TELEGRAM_CHAT_BOT_TOKEN and ADMIN_CHAT_BOT_CHAT_ID:
            telegram_msg = (
                f"🛍️ <b>New Chat Booking!</b>\n\n"
                f"👤 <b>Customer:</b> {customer_name}\n"
                f"📞 <b>Phone:</b> {customer_phone}\n"
                f"👗 <b>Product:</b> {product_name}\n"
                f"📏 <b>Size:</b> {size}\n"
                f"💰 <b>Price:</b> ₹{price}\n"
                f"💬 <b>Message:</b> <i>{message or 'No message'}</i>\n\n"
                f"🆔 <b>Chat ID:</b> <code>{customer_chat_id}</code>\n\n"
                f"💡 <i>Reply here or use /send {customer_chat_id} your_reply</i>"
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
            
            try:
                chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                keyboard = InlineKeyboardMarkup()
                for btn_row in buttons:
                    row_buttons = []
                    for btn in btn_row:
                        row_buttons.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["data"]))
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
                    except Exception:
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
                print("📢 Chat Bot message sent to admin")
            except Exception as e:
                print(f"❌ Chat Bot error: {e}")
                
        whatsapp_msg = (
            f"🛍️ *New Chat Booking*\n\n"
            f"👤 {customer_name}\n"
            f"📞 {customer_phone}\n"
            f"👗 {product_name} (Size: {size})\n"
            f"💰 ₹{price}\n\n"
            f"👉 Check Telegram Chat Bot for buttons!"
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

# 🆕 Customer sends message → forwarded to Telegram
@app.post("/api/send-customer-message")
async def send_customer_message(
    customer_chat_id: str = Form(...),
    message: str = Form(...)
):
    try:
        if not message.strip():
            return {"status": "error", "detail": "Empty message"}
        
        current_time = time.time()
        
        if chat_messages_table is not None:
            chat_messages_table.insert_one({
                "customer_chat_id": customer_chat_id,
                "from": "customer",
                "message": message,
                "timestamp": current_time,
                "type": "customer_message",
                "read": False
            })
            
        booking = bookings_table.find_one({"customer_chat_id": customer_chat_id}) if bookings_table is not None else None
        c_name = booking["customer_name"] if booking else "Customer"
        c_phone = booking["customer_phone"] if booking else "Unknown"
        
        if TELEGRAM_CHAT_BOT_TOKEN and ADMIN_CHAT_BOT_CHAT_ID:
            try:
                chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                telegram_text = (
                    f"💬 <b>New Message from {c_name}</b>\n"
                    f"📞 {c_phone}\n"
                    f"🆔 <code>{customer_chat_id}</code>\n\n"
                    f"💭 {message}\n\n"
                    f"👆 <i>Reply to this message to send back to customer</i>\n"
                    f"📝 <i>Or use: /send {customer_chat_id} your_message</i>"
                )
                chat_bot.send_message(
                    chat_id=ADMIN_CHAT_BOT_CHAT_ID,
                    text=telegram_text,
                    parse_mode="HTML"
                )
                print(f"✅ Customer message forwarded to Telegram: {customer_chat_id}")
            except Exception as e:
                print(f"❌ Telegram forward error: {e}")
            
        return {"status": "success", "timestamp": current_time}
    except Exception as e:
        print(f"❌ Error forwarding customer message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🆕 Get chat messages with polling support
@app.get("/api/chat/{customer_chat_id}/messages")
def get_chat_messages(customer_chat_id: str, since: float = 0):
    try:
        if chat_messages_table is None:
            return {"status": "error", "messages": [], "booking_status": "unknown"}

        query = {"customer_chat_id": customer_chat_id}
        if since > 0:
            query["timestamp"] = {"$gt": since}

        messages = list(
            chat_messages_table.find(query).sort("timestamp", 1)
        )

        booking = bookings_table.find_one({"customer_chat_id": customer_chat_id}) if bookings_table is not None else None
        booking_status = booking.get("status", "pending") if booking else "unknown"

        unread_count = 0
        if since > 0:
            unread_count = chat_messages_table.count_documents({
                "customer_chat_id": customer_chat_id,
                "from": "admin",
                "timestamp": {"$gt": since},
                "read": False
            })
            chat_messages_table.update_many(
                {
                    "customer_chat_id": customer_chat_id,
                    "from": "admin",
                    "timestamp": {"$gt": since},
                    "read": False
                },
                {"$set": {"read": True}}
            )

        return {
            "status": "success",
            "booking_status": booking_status,
            "messages": [
                {
                    "from": msg["from"],
                    "message": msg["message"],
                    "timestamp": msg["timestamp"],
                    "type": msg.get("type", "text")
                }
                for msg in messages
            ],
            "unread_count": unread_count
        }
    except Exception as e:
        print(f"❌ Get messages error: {e}")
        return {"status": "error", "messages": [], "booking_status": "unknown"}


# 🛍️ Bookings API (Legacy)
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
            f"👋 *Welcome to Dolphin Trends!* 🐬\n\n"
            f"Hi *{payload.customer_name}*,\n"
            f"You have selected:\n"
            f"👗 *{payload.product_name}*\n"
            f"📏 Size: *{payload.size}*\n"
            f"💰 Price: *{payload.price}*\n\n"
            f"⏳ *We are currently checking the stock availability for your order.* \n"
            f"Our team will contact you shortly with confirmation. 🙏\n\n"
            f"✨ *Meanwhile, explore our latest collections here:* 👇\n"
            f"🔗 {FRONTEND_URL}\n\n"
            f"Thank you for choosing us 😊\n"
            f"🏢 *Team Dolphin Trends* 🐬"
        )
        send_whatsapp_msg(payload.customer_phone, customer_message)
        
        admin_message = (
            f"🛍️ *New Buy Request Boss*😎\n\n"
            f"👗 *Product:* {payload.product_name}\n"
            f"📏 *Size:* {payload.size}\n"
            f"💰 *Price:* {payload.price}\n"
            f"👤 *Name:* {payload.customer_name}\n"
            f"📞 *Phone:* {payload.customer_phone}\n\n"
            f"⚙️ 🛠️ *Plz Update in Admin Panel Boss* 👇\n"
            f"🔗 {FRONTEND_URL}"
        )
        send_whatsapp_to_admins(admin_message)
        
        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 👗 Products API
@app.post("/products")
async def add_product(
    name: str = Form(...),
    price: str = Form(...),
    original_price: str = Form(None),
    discount_percent: str = Form(None),
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
            if len(file_bytes) > 100:
                cloud_image_url = upload_to_cloudinary(file_bytes, is_file=True)
                if not cloud_image_url:
                    raise HTTPException(status_code=500, detail="Image upload failed!")
            else:
                raise HTTPException(status_code=400, detail="Empty file!")
        else:
            raise HTTPException(status_code=400, detail="Please upload a product image!")
        
        # 🆕 Auto-calculate discount fields
        current_price_num = int(re.sub(r'[^0-9]', '', price)) if price else 0
        original_price_num = int(re.sub(r'[^0-9]', '', original_price)) if original_price else 0
        discount_pct = int(discount_percent) if discount_percent else 0
        
        if original_price_num > 0 and discount_pct == 0:
            discount_pct = round(((original_price_num - current_price_num) / original_price_num) * 100)
        elif discount_pct > 0 and original_price_num == 0:
            original_price_num = round(current_price_num / (1 - discount_pct / 100))
            
        new_id = str(uuid.uuid4())[:8]
        products_table.insert_one({
            "id": new_id, "product_id": new_id,
            "name": name, 
            "price": price, 
            "original_price": f"₹{original_price_num}" if original_price_num > 0 else "",
            "discount_percent": discount_pct,
            "category": category, 
            "description": description or "",
            "image": cloud_image_url, 
            "available": is_available
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
        customer_chat_id = booking.get("customer_chat_id", "")
        
        if action == "agree":
            msg = (
                f"Hello {c_name}! ✅\n\n"
                f"Good news 🌟! *{p_name}* is available at Dolphin Trends\n\n"
                f"🛍️ *Please visit our shop to collect your product* 👇\n\n"
                f"🏢 *Store Address:*\n"
                f"Rajgopal Nagar Main Road, Peenya 2nd Stage, Bangalore\n\n"
                f"🕒 *Timings:* 11:00 AM - 10:00 PM\n"
                f"📞 *Phone:* 9353344035\n\n"
                f"See you soon! 🛍️\n\n👤 *Team Dolphin Trends* 🐬"
            )
            
            if chat_messages_table is not None and customer_chat_id:
                chat_messages_table.insert_one({
                    "customer_chat_id": customer_chat_id,
                    "from": "admin",
                    "message": msg,
                    "timestamp": time.time(),
                    "type": "status_update",
                    "read": False
                })
                
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved"}})
            
        elif action == "disagree":
            msg = (
                f"Hello {c_name}!\n\n"
                f"Sorry 😔, *{p_name}* is currently out of stock.\n"
                f"We'll notify you when it's back 😢\n"
                f"Thank you for choosing us..😊\n\n"
                f"👤 *Team Dolphin Trends* 🐬"
            )
            
            if chat_messages_table is not None and customer_chat_id:
                chat_messages_table.insert_one({
                    "customer_chat_id": customer_chat_id,
                    "from": "admin",
                    "message": msg,
                    "timestamp": time.time(),
                    "type": "status_update",
                    "read": False
                })
                
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})
            
        elif action == "size_unavail" or action == "size_no_stock":
            msg = (
                f"Hello {c_name}!\n\n"
                f"Sorry 😔, your requested size for *{p_name}* is currently unavailable.\n"
                f"Please select another size or checkout other items!\n\n"
                f"Thank you for choosing us..😊\n\n"
                f"👤 *Team Dolphin Trends* 🐬"
            )
            if chat_messages_table is not None and customer_chat_id:
                chat_messages_table.insert_one({
                    "customer_chat_id": customer_chat_id,
                    "from": "admin",
                    "message": msg,
                    "timestamp": time.time(),
                    "type": "status_update",
                    "read": False
                })
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Size Unavailable"}})
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# 🌐 TELEGRAM WEBHOOK - COMPLETELY REWRITTEN WITH ALL FIXES
# ============================================================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        
        # 🎮 Handle Chat Bot callback queries (inline buttons)
        if "callback_query" in data:
            return await handle_chat_bot_callback(data)
            
        if "message" not in data:
            return {"status": "ok"}
            
        message = data["message"]
        chat_id = message["chat"]["id"]
        message_text = message.get("text", "").strip()
        
        # =========================================================
        # 💬 SCENARIO 1: ADMIN REPLIES TO A MESSAGE (Reply feature)
        # =========================================================
        if "reply_to_message" in message and "text" in message:
            reply_to = message["reply_to_message"]
            admin_reply_text = message["text"]
            
            parent_text = reply_to.get("text") or reply_to.get("caption") or ""
            
            # ✅ FIXED: Multiple regex patterns in priority order
            match = re.search(r'<code>([a-f0-9]{12})</code>', parent_text)
            if not match:
                match = re.search(r'🆔[^a-f0-9]*([a-f0-9]{12})', parent_text)
            if not match:
                match = re.search(r'Chat ID:?\s*([a-f0-9]{12})', parent_text)
            if not match:
                match = re.search(r'([a-f0-9]{12})', parent_text)
            
            if match:
                customer_chat_id = match.group(1)
                
                if chat_messages_table is not None:
                    chat_messages_table.insert_one({
                        "customer_chat_id": customer_chat_id,
                        "from": "admin",
                        "message": admin_reply_text,
                        "timestamp": time.time(),
                        "type": "admin_reply",
                        "read": False
                    })
                    print(f"✅ Admin reply forwarded to chat box: {customer_chat_id}")
                    
                    try:
                        chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                        chat_bot.reply_to(message, "🚀 Forwarded to Customer Chat Box!")
                    except Exception:
                        pass
                    return {"status": "success", "type": "reply_forwarded"}
        
        # =========================================================
        # 💬 SCENARIO 2: ADMIN USES /send COMMAND
        # =========================================================
        if message_text.startswith("/send "):
            # 🆕 Rate limiting
            if not check_rate_limit(chat_id, "send", cooldown_seconds=3):
                try:
                    chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                    chat_bot.send_message(
                        chat_id=chat_id,
                        text="⏰ Please wait 3 seconds between messages!"
                    )
                except Exception:
                    pass
                return {"status": "rate_limited"}
            
            send_match = re.match(r'^/send\s+([a-f0-9]{12})\s+(.+)$', message_text, re.DOTALL)
            if send_match:
                customer_chat_id = send_match.group(1)
                admin_message_text = send_match.group(2)
                
                booking = bookings_table.find_one({"customer_chat_id": customer_chat_id}) if bookings_table is not None else None
                if not booking:
                    try:
                        chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                        # ✅ FIXED: Use HTML <code> tag instead of backticks
                        chat_bot.send_message(
                            chat_id=chat_id,
                            text=f"❌ Chat ID <code>{customer_chat_id}</code> not found!",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
                    return {"status": "chat_not_found"}
                
                if chat_messages_table is not None:
                    chat_messages_table.insert_one({
                        "customer_chat_id": customer_chat_id,
                        "from": "admin",
                        "message": admin_message_text,
                        "timestamp": time.time(),
                        "type": "admin_reply",
                        "read": False
                    })
                    print(f"✅ Admin /send command forwarded: {customer_chat_id}")
                    
                    try:
                        chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                        chat_bot.send_message(
                            chat_id=chat_id,
                            text=f"✅ Sent to customer <code>{customer_chat_id}</code>:\n\n{admin_message_text}",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
                    return {"status": "success", "type": "send_command"}
            else:
                # Invalid format
                try:
                    chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                    chat_bot.send_message(
                        chat_id=chat_id,
                        text=(
                            "❌ Invalid format!\n\n"
                            "✅ Correct format:\n"
                            "<code>/send CHAT_ID your_message</code>\n\n"
                            "Example:\n"
                            "<code>/send e61e9e773ec Hello! Your order is ready</code>"
                        ),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                return {"status": "invalid_format"}
        
        # =========================================================
        # 💬 SCENARIO 3: BROADCAST TO ALL CUSTOMERS
        # =========================================================
        if message_text.startswith("/sendall "):
            # 🆕 Rate limiting - 5 minutes for broadcasts
            if not check_rate_limit(chat_id, "broadcast", cooldown_seconds=300):
                try:
                    chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                    chat_bot.send_message(
                        chat_id=chat_id,
                        text="⏰ Please wait 5 minutes between broadcasts!"
                    )
                except Exception:
                    pass
                return {"status": "rate_limited"}
            
            broadcast_msg = message_text.replace("/sendall ", "", 1)
            if broadcast_msg and chat_messages_table is not None and bookings_table is not None:
                active_chats = bookings_table.distinct("customer_chat_id")
                sent_count = 0
                for cc_id in active_chats:
                    if cc_id:
                        chat_messages_table.insert_one({
                            "customer_chat_id": cc_id,
                            "from": "admin",
                            "message": broadcast_msg,
                            "timestamp": time.time(),
                            "type": "broadcast",
                            "read": False
                        })
                        sent_count += 1
                
                try:
                    chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                    chat_bot.send_message(
                        chat_id=chat_id,
                        text=f"📢 Broadcast sent to {sent_count} customers!\n\nMessage: {broadcast_msg}"
                    )
                except Exception:
                    pass
                return {"status": "success", "type": "broadcast", "count": sent_count}
        
        # =========================================================
        # 💬 SCENARIO 4: LIST ACTIVE CHATS
        # =========================================================
        if message_text == "/list":
            if bookings_table is not None:
                active_bookings = list(bookings_table.find().sort("created_at", -1).limit(10))
                if active_bookings:
                    list_text = "📋 <b>Recent Active Chats:</b>\n\n"
                    for b in active_bookings:
                        list_text += (
                            f"🆔 <code>{b.get('customer_chat_id', 'N/A')}</code>\n"
                            f"👤 {b.get('customer_name', 'Unknown')}\n"
                            f"📞 {b.get('customer_phone', 'N/A')}\n"
                            f"👗 {b.get('product_name', 'N/A')}\n"
                            f"📊 Status: {b.get('status', 'pending')}\n"
                            f"{'─'*20}\n"
                        )
                    list_text += "\n💡 <i>Use: /send CHAT_ID your_message</i>"
                else:
                    list_text = "📭 No active chats found."
                
                try:
                    chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                    chat_bot.send_message(chat_id=chat_id, text=list_text, parse_mode="HTML")
                except Exception:
                    pass
            return {"status": "success", "type": "list"}
        
        # =========================================================
        # 💬 SCENARIO 5: HELP COMMAND
        # =========================================================
        if message_text in ["/help", "/start"]:
            help_text = (
                "🤖 <b>Chat Bot Commands:</b>\n\n"
                "1️⃣ <b>Reply to customer message</b>\n"
                "   → Just reply, it auto-forwards\n\n"
                "2️⃣ <b>/send CHAT_ID message</b>\n"
                "   → Send to specific customer\n"
                "   → Example: <code>/send e61e9e773ec Hello</code>\n\n"
                "3️⃣ <b>/sendall message</b>\n"
                "   → Broadcast to all customers\n\n"
                "4️⃣ <b>/list</b>\n"
                "   → Show recent active chats\n\n"
                "5️⃣ <b>/help</b>\n"
                "   → Show this help"
            )
            try:
                chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                chat_bot.send_message(chat_id=chat_id, text=help_text, parse_mode="HTML")
            except Exception:
                pass
            return {"status": "success", "type": "help"}
        
        # =========================================================
        # 💬 SCENARIO 6: STATS COMMAND (NEW)
        # =========================================================
        if message_text == "/stats":
            if bookings_table is not None and chat_messages_table is not None:
                total_bookings = bookings_table.count_documents({})
                pending = bookings_table.count_documents({"status": "pending"})
                approved = bookings_table.count_documents({"status": "Approved"})
                total_messages = chat_messages_table.count_documents({})
                
                stats_text = (
                    "📊 <b>Bot Statistics:</b>\n\n"
                    f"📦 Total Bookings: <b>{total_bookings}</b>\n"
                    f"⏳ Pending: <b>{pending}</b>\n"
                    f"✅ Approved: <b>{approved}</b>\n"
                    f"💬 Total Messages: <b>{total_messages}</b>\n"
                )
                
                try:
                    chat_bot = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                    chat_bot.send_message(chat_id=chat_id, text=stats_text, parse_mode="HTML")
                except Exception:
                    pass
            return {"status": "success", "type": "stats"}
        
        # =========================================================
        # 📸 HANDLE UPLOAD BOT (Bot 1) PHOTOS
        # =========================================================
        
        # ALLOWED_USERS check - only for upload bot
        if ALLOWED_USERS and chat_id not in ALLOWED_USERS:
            return {"status": "Ignored"}
        
        if "photo" not in message:
            return {"status": "ok"}
            
        # 📸 Handle Upload Bot photos
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
            price_match = re.search(r'(?:Rs\.?|₹|\$)?\s*?(\d{3,5})', clean_text)
            
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
                remaining_text = clean_text.replace(price_match.group(0), "").replace("₹", "").strip()
                if len(remaining_text) > 2:
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
            elif caption:
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
        if products_table is not None:
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
            json={"chat_id": chat_id, "text": f"✅ Saved: {product_name} | {product_price_display}"},
            timeout=5
        )
        return {"status": "success"}
    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"status": "error"}

async def handle_chat_bot_callback(data):
    """💬 Chat Bot (Bot 2) button click handler - With auto-delete buttons"""
    try:
        callback = data["callback_query"]
        callback_data = callback["data"]
        callback_id = callback["id"]
        message_id = callback["message"]["message_id"]
        chat_id = callback["message"]["chat"]["id"]
        
        print(f"🔘 Chat Bot button clicked: {callback_data}")
        
        parts = callback_data.split("_", 1)
        if len(parts) != 2:
            return {"status": "invalid"}
            
        action, customer_chat_id = parts[0], parts[1]
        
        booking = bookings_table.find_one({"customer_chat_id": customer_chat_id}) if bookings_table is not None else None
        if not booking:
            try:
                chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                chat_bot_instance.answer_callback_query(callback_id, "❌ Booking not found", show_alert=True)
                return {"status": "not found"}
            except Exception:
                return {"status": "not found"}
                
        c_name = booking["customer_name"]
        c_phone = booking["customer_phone"]
        p_name = booking["product_name"]
        booking_id = booking.get("booking_id", "")
        
        # ✅ CHECK: If already processed, ignore duplicate clicks
        current_status = booking.get("status", "pending")
        if current_status in ["Approved", "Out of Stock", "Size Unavailable"]:
            try:
                chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                chat_bot_instance.answer_callback_query(
                    callback_id, 
                    f"⚠️ Already processed as {current_status}!", 
                    show_alert=True
                )
            except Exception:
                pass
            return {"status": "already_processed"}
        
        # ✅ Show "processing" alert immediately
        try:
            chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
            chat_bot_instance.answer_callback_query(
                callback_id, 
                f"⏳ Processing {action.upper()}...", 
                show_alert=False
            )
        except Exception:
            pass
        
        # ✅ Process the action
        status_action = ""
        status_text = ""
        status_emoji = ""
        
        if action == "approve":
            status_action = "agree"
            status_text = "APPROVED"
            status_emoji = "🟢"
        elif action == "reject":
            status_action = "disagree"
            status_text = "DISAGREED"
            status_emoji = "🔴"
        elif action == "sizeno":
            status_action = "size_no_stock"
            status_text = "SIZE UNAVAILABLE"
            status_emoji = "🟡"
            
        if status_action and booking_id:
            update_booking_status(booking_id, status_action)
        
        # ✅✅✅ KEY FIX: EDIT THE MESSAGE TO REMOVE BUTTONS ✅✅✅
        try:
            chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
            
            original_msg = callback["message"]
            original_text = original_msg.get("text") or original_msg.get("caption", "")
            
            new_text = (
                f"{original_text}\n\n"
                f"{'='*30}\n"
                f"{status_emoji} <b>STATUS: {status_text}</b>\n"
                f"👤 Processed for: {c_name}\n"
                f"📞 {c_phone}\n"
                f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"{'='*30}\n\n"
                f"✅ <i>Buttons removed. Action completed.</i>\n"
                f"<i>Customer will be notified in chat box.</i>"
            )
            
            if "caption" in original_msg:
                chat_bot_instance.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=new_text,
                    parse_mode='HTML',
                    reply_markup=None
                )
            else:
                chat_bot_instance.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=new_text,
                    parse_mode='HTML',
                    reply_markup=None
                )
            
            print(f"✅ Buttons removed from message {message_id}")
            
        except Exception as e:
            print(f"⚠️ Could not edit message: {e}")
            try:
                chat_bot_instance = telebot.TeleBot(TELEGRAM_CHAT_BOT_TOKEN)
                chat_bot_instance.send_message(
                    chat_id=chat_id,
                    text=f"{status_emoji} {status_text} - {c_name} ({p_name})\n⏰ {time.strftime('%H:%M:%S')}",
                )
            except Exception:
                pass
        
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Chat Callback Error: {e}")
        return {"status": "error"}
