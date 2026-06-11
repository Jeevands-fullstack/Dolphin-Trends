import os
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import certifi
import cloudinary
import cloudinary.uploader
import base64

# ================= CONFIGURATION =================
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "https://dolphin-trends-3.onrender.com"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"
YOUR_WHATSAPP_GROUP_ID = os.getenv("YOUR_WHATSAPP_GROUP_ID", "120363293847291048@g.us")

CLOUDINARY_CLOUD_NAME = "diqwkall4"
CLOUDINARY_API_KEY_VAL = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY_VAL,
    api_secret=CLOUDINARY_API_SECRET
)

# ================= DATABASE =================
ca = certifi.where()
db = None
products_table = None

if MONGO_URL:
    client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
    db = client["dolphin_trends_db"]
    products_table = db["products"]

# ================= WHATSAPP HELPER (PRICE REMOVED) =================
def send_whatsapp(image_url, name, description):
    try:
        # Caption with Description, no Price
        caption = (
            "🛍️ *Dolphin Trends - New Arrival!*\n\n"
            f"👕 *Product:* {name}\n"
            f"📝 *Details:* {description}\n\n"
            f"🌐 *View Price & Shop Now:*\n{FRONTEND_URL}"
        )
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": YOUR_WHATSAPP_GROUP_ID,
            "urlFile": image_url,
            "caption": caption
        }
        requests.post(url, json=payload, timeout=30)
        print("✅ WhatsApp message sent successfully!")
    except Exception as e:
        print("WhatsApp Error:", e)

# ================= LIFESPAN & APP =================
@asynccontextmanager
async def lifespan(app: FastAPI):
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook")
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook", json={"url": f"{BACKEND_URL}/webhook"})
            print("✅ Telegram webhook set successfully")
        except Exception as e:
            print("Webhook setup error:", e)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ================= HELPERS =================
def upload_to_cloudinary(image_source):
    try:
        result = cloudinary.uploader.upload(image_source, folder="dolphin_trends", resource_type="image")
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Error: {e}")
        return None

# ================= WEBHOOK ROUTE =================
@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if "message" in data and "photo" in data["message"]:
            msg = data["message"]
            caption = msg.get("caption", "New Product")
            file_id = msg["photo"][-1]["file_id"]
            
            f_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile", params={"file_id": file_id}).json()
            f_path = f_info.get("result", {}).get("file_path")
            img_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{f_path}"
            
            perm_url = upload_to_cloudinary(img_url)
            
            if perm_url and products_table is not None:
                # Save to DB
                product_data = {
                    "name": caption.split('\n')[0].strip(),
                    "description": "Curated boutique wear.",
                    "image": perm_url,
                    "available": True
                }
                products_table.insert_one(product_data)
                
                # WhatsApp background task (No price)
                background_tasks.add_task(send_whatsapp, perm_url, product_data["name"], product_data["description"])
                
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error"}

@app.get("/")
def home():
    return {"status": "Dolphin Trends Backend Active!"}
