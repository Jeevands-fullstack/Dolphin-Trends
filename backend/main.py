from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tinydb import TinyDB, Query
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

def send_whatsapp(image_url, display_name):
    try:
        # 🎯 ಜೀವನ್, ವಾಟ್ಸಾಪ್‌ಗೆ ಕಳುಹಿಸುವ ಹೆಸರಿನಿಂದ ನಂಬರ್‌ಗಳನ್ನು (250, 350, 1200) ಕಂಪ್ಲೀಟ್ ಆಗಿ ತೆಗೆದುಹಾಕುವ ಲಾಜಿಕ್:
        clean_name = re.sub(r'\d+', '', display_name).replace('Rs.', '').strip()
        # ಡಬಲ್ ಸ್ಪೇಸ್ ಇದ್ದರೆ ಸಿಂಗಲ್ ಸ್ಪೇಸ್ ಮಾಡೋದು
        clean_name = " ".join(clean_name.split())
        
        # ಮೊದಲನೇ ಅಕ್ಷರ ಕ್ಯಾಪಿಟಲ್ ಮಾಡೋದು
        clean_name = clean_name.title()

        caption = (
            f"🔥 *Hurry! Limited Stock!*\n\n"
            f"✨ *New Arrival: Premium {clean_name}*\n"
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
        requests.post(url, json=payload, timeout=60)
        return True
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= HEALTH =================

@app.get("/")
def home():
    return {"status": "Dolphin Trends Backend - Perfect Number Filter Active"}

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
        product_name = ""
        input_price = None

        if len(lines) > 0:
            category = lines[0].strip()
        
        for line in lines:
            if 'price' in line.lower():
                match = re.search(r'price\s*:\s*(\d+)', line.lower())
                if match:
                    input_price = int(match.group(1))

        # ಪ್ರೈಸ್ ಲೈನ್ ಅಲ್ಲದ ಬೇರೆ ಹೆಸರುಗಳಿದ್ದರೆ ತಗೊಳ್ಳುತ್ತೆ
        name_parts = []
        for line in lines[1:]:
            if 'price' not in line.lower():
                name_parts.append(line)
        
        if name_parts:
            product_name = " ".join(name_parts)
        else:
            product_name = category

        # ಪ್ರೈಸ್ ಇಲ್ಲದಿದ್ದರೆ ಡಿಫಾಲ್ಟ್ ಚೆಕ್
        if input_price is None:
            cat_lower = category.lower().strip()
            input_price = DEFAULT_PRICES.get(cat_lower, 0)

        calculated_original = int(input_price * 1.40)

        # Download original image from Telegram
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile", params={"file_id": file_id}).json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        downloaded_photo = requests.get(file_url).content

        # SAVE IMAGE
        filename = str(uuid.uuid4()) + ".jpg"
        filepath = f"uploads/{filename}"
        
        img_file = io.BytesIO(downloaded_photo)
        image_pil = Image.open(img_file)
        if image_pil.mode in ("RGBA", "P"):
            image_pil = image_pil.convert("RGB")
        image_pil.save(filepath, "JPEG", quality=85, optimize=True)

        final_image_url = f"{BACKEND_URL}/uploads/{filename}"

        # Database insert (ಕ್ಯಾಟಗರಿ ಹೆಸರು ಬಾಕ್ಸ್‌ಗೆ ಮ್ಯಾಚ್ ಆಗೋ ತರಹ '250 tops' ಅಂತಾನೇ ಇರುತ್ತೆ)
        product = {
            "id": str(uuid.uuid4()),
            "name": product_name,
            "price": "Rs." + str(input_price),
            "original_price": "Rs." + str(calculated_original),
            "description": f"Premium {product_name} from Dolphin Trends",
            "category": category,  
            "image": final_image_url,
            "available": True
        }
        products_table.insert(product)

        # WhatsApp share (ಇಲ್ಲಿ ಇಂಟೆಲಿಜೆಂಟ್ ಆಗಿ ನಂಬರ್ ಡಿಲೀಟ್ ಆಗಿ ಹೋಗುತ್ತೆ)
        send_whatsapp(final_image_url, product_name)

        send_telegram(chat_id, f"✅ Done!\n📂 Category: {category}\n✨ Sent to WhatsApp (Price Hidden!)\n🌐 {FRONTEND_URL}")
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
    products_table.remove(Product.id == product_id)
    return {"success": True}
