from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tinydb import TinyDB, Query
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import uuid
import requests
import json
import re
import io
from PIL import Image

# ================= FASTAPI =================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DATABASE =================

db = TinyDB("database.json")
products_table = db.table("products")
bookings_table = db.table("bookings")
reviews_table = db.table("reviews")

# ================= UPLOAD FOLDER =================

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ================= ENV VARIABLES =================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GREEN_API_ID = os.environ.get("GREEN_API_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "917411255628@c.us")
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"
BACKEND_URL = "https://dolphin-trends-3.onrender.com"

# ================= DEFAULT PRICES =================

DEFAULT_PRICES = {
    "leggings": 200,
    "kurtha top": 200,
    "umbrella sets": 1000,
    "kurta sets": 1200,
    "jeans": 550,
    "jeans tops": 300,
    "frocks": 850,
    "250 tops": 250,
    "350 tops": 350,
    "gym pants": 300,
    "patiala pants": 200
}

# ================= HELPERS =================

def send_telegram(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def send_whatsapp(image_url, name):
    try:
        # 🔥 ಜೀವನ್, ಇಲ್ಲಿ ವಾಟ್ಸಾಪ್ ಕ್ಯಾಪ್ಷನ್ ಪಕ್ಕಾ ಬ್ಯುಸಿನೆಸ್ ಲುಕ್ ಕೊಡುತ್ತೆ, ಯಾವುದೇ ಪ್ರೈಸ್ ಬರಲ್ಲ
        caption = (
            f"🔥 *Hurry! Limited Stock!*\n\n"
            f"✨ *New Arrival: {name}*\n"
            f"💃 *Grab yours before it's gone!*\n\n"
            f"👇 *Check Price & Shop Now:*\n{FRONTEND_URL}"
        )
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": WHATSAPP_NUMBER,
            "urlFile": image_url,
            "fileName": "product.jpg",
            "caption": caption
        }
        response = requests.post(url, json=payload, timeout=60)
        return response.status_code == 200
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= HEALTH =================

@app.get("/")
def home():
    return {"status": "Dolphin Trends Backend - Absolute Price Stripper Active"}

# ================= WEBHOOK SETUP =================

@app.on_event("startup")
async def startup():
    webhook_url = f"{BACKEND_URL}/webhook"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook", json={"url": webhook_url})

# ================= TELEGRAM WEBHOOK =================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        if not chat_id or "photo" not in message:
            return {"ok": True}

        send_telegram(chat_id, "📥 Photo received...")
        caption = message.get("caption", "").strip()

        # ಲೈನ್ ಬೈ ಲೈನ್ ಕ್ಲೀನ್ ಪಾರ್ಸಿಂಗ್
        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        
        category = "Kurta Sets"  
        name = ""
        input_price = None

        # 1. ಮೊದಲನೇ ಲೈನ್‌ನಿಂದ ಕ್ಯಾಟಗರಿ ಹೆಸರು ತಗೋಳೋದು
        if len(lines) > 0:
            category = lines[0].strip()
        
        # ಪ್ರೈಸ್ ಲೈನ್ ಪಾರ್ಸಿಂಗ್
        for line in lines:
            if 'price' in line.lower():
                match = re.search(r'price\s*:\s*(\d+)', line.lower())
                if match:
                    try:
                        input_price = int(match.group(1))
                    except Exception as e:
                        print("Price parse error:", e)

        # 🎯 2. ಜೀವನ್, ವಾಟ್ಸಾಪ್ ಹೆಸರಿಗೆ ಪ್ರೈಸ್ ಲೈನ್ ಆಡ್ ಆಗದ ಹಾಗೆ ಪಕ್ಕಾ ಫಿಲ್ಟರ್:
        valid_name_lines = []
        for line in lines[1:]: 
            # ಯಾವ ಲೈನ್‌ನಲ್ಲಿ 'price' ಅನ್ನೋ ಪದ ಇರುತ್ತೋ, ಆ ಲೈನ್ ಕಂಪ್ಲೀಟ್ ಆಗಿ ಬಿಟ್ಟುಬಿಡುತ್ತೆ!
            if 'price' not in line.lower():
                valid_name_lines.append(line)
        
        if valid_name_lines:
            name = " ".join(valid_name_lines)
        else:
            if category:
                name = "Premium " + category
            else:
                category = "Kurta Sets"
                name = "Premium Collection"

        # ಡಿಫಾಲ್ಟ್ ಪ್ರೈಸ್ ಚೆಕ್
        if input_price is None:
            cat_lower = category.lower().strip()
            input_price = DEFAULT_PRICES.get(cat_lower, 0)

        # 40% ಮಾರ್ಕಪ್ ಕ್ಯಾಲ್ಕುಲೇಷನ್
        calculated_original = int(input_price * 1.40)
        
        price = str(input_price)
        original_price = str(calculated_original)

        # Download original image from Telegram
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile", params={"file_id": file_id}).json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        downloaded_photo = requests.get(file_url).content

        description = f"Premium {name} from Dolphin Trends"

        # SAVE IMAGE
        send_telegram(chat_id, "🚀 Saving original image and uploading...")
        filename = str(uuid.uuid4()) + ".jpg"
        filepath = f"uploads/{filename}"
        
        img_file = io.BytesIO(downloaded_photo)
        image_pil = Image.open(img_file)
        if image_pil.mode in ("RGBA", "P"):
            image_pil = image_pil.convert("RGB")
        image_pil.save(filepath, "JPEG", quality=85, optimize=True)

        # Database insert
        product = {
            "id": str(uuid.uuid4()),
            "name": name,
            "price": "Rs." + price,
            "original_price": "Rs." + original_price,
            "description": description,
            "category": category,  
            "image": f"{BACKEND_URL}/uploads/{filename}",
            "available": True
        }
        products_table.insert(product)

        # WhatsApp share
        send_whatsapp(product["image"], name)

        send_telegram(chat_id, f"✅ Product Active!\n📂 Website Box Category: {category}\n✨ WhatsApp Sent (Price Hidden!)\n🌐 {FRONTEND_URL}")

        return {"ok": True}
    except Exception as e:
        print("Error:", str(e))
        return {"ok": True}

# ================= PRODUCTS ENDPOINTS =================

@app.get("/products")
def get_products():
    return products_table.all()

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    Product = Query()
    existing = products_table.search(Product.id == product_id)
    if not existing:
        return {"error": "Product not found"}
    try:
        image_url = existing[0].get("image", "")
        if "uploads/" in image_url:
            filename = image_url.split("uploads/")[-1]
            filepath = f"uploads/{filename}"
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception as e:
        print(e)
    products_table.remove(Product.id == product_id)
    return {"success": True}
