import os
import uuid
import time
import requests
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
import google.generativeai as genai
import cloudinary
import cloudinary.uploader

# bot.py ನಿಂದ Instagram ಆಟೋಮೇಷನ್ ಫಂಕ್ಷನ್ ಇಂಪೋರ್ಟ್
from bot import send_instagram_direct

# 🌐 MongoDB & Global Variables Configuration
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "https://dolphin-trends-3.onrender.com"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"
INSTAGRAM_URL = "https://www.instagram.com/dolphin_trends"

CLOUDINARY_CLOUD_NAME = "diqwkall4"
CLOUDINARY_API_KEY_VAL = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY_VAL,
    api_secret=CLOUDINARY_API_SECRET
)

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

raw_users = os.getenv("ALLOWED_USERS", "2113728041")
ALLOWED_USERS = [int(uid.strip()) for uid in raw_users.split(",") if uid.strip().isdigit()]

YOUR_PERSONAL_PHONE = os.getenv("YOUR_PERSONAL_PHONE", "917411255628")
YOUR_WHATSAPP_GROUP_ID = os.getenv("YOUR_WHATSAPP_GROUP_ID", "120363293847291048@g.us")

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook")
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook", json={"url": f"{BACKEND_URL}/webhook"})
        except Exception as e:
            print("Webhook setup error:", e)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🛠️ Helper Functions
def upload_to_cloudinary(image_source):
    try:
        result = cloudinary.uploader.upload(image_source, folder="dolphin_trends", resource_type="image")
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Error: {e}")
        return None

def send_whatsapp_image(image_url, product_name):
    try:
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {"chatId": YOUR_WHATSAPP_GROUP_ID, "urlFile": image_url, "caption": f"New Arrival: {product_name}"}
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print("WhatsApp Error:", e)

# 🚀 Webhook Handler with Background Task
@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if "message" in data and "photo" in data["message"]:
        msg = data["message"]
        file_id = msg["photo"][-1]["file_id"]
        
        # Get file path
        f_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile", params={"file_id": file_id}).json()
        f_path = f_info.get("result", {}).get("file_path")
        img_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{f_path}"
        
        # Upload to Cloudinary & DB
        perm_url = upload_to_cloudinary(img_url)
        if perm_url:
            products_table.insert_one({"name": "New Product", "image": perm_url, "available": True})
            send_whatsapp_image(perm_url, "New Product")
            
            # 📸 [UPDATED]: Background task for Instagram
            img_data = requests.get(perm_url).content
            background_tasks.add_task(send_instagram_direct, img_data, "New Product", "Sets")
            
    return {"status": "ok"}

@app.get("/")
def home():
    return {"status": "Dolphin Trends Backend Active!"}
