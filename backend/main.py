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
import urllib.parse
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
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
        # ವಾಟ್ಸಾಪ್ ಕ್ಯಾಪ್ಷನ್ - ಕೇವಲ ಬಟ್ಟೆಯ ಹೆಸರು ಮಾತ್ರ ಇರುತ್ತೆ
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
    return {"status": "Dolphin Trends Backend - Absolute Price Filter Active"}

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
        
        is_edit_requested = "#edit" in caption.lower()

        # ಲೈನ್ ಬೈ ಲೈನ್ ಕ್ಲೀನ್ ಪಾರ್ಸಿಂಗ್
        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        
        category = "Kurta Sets"
        name = ""
        input_price = None

        if len(lines) > 0:
            category = lines[0].replace("#edit", "").strip()
        
        # 🎯 1. ಪ್ರೈಸ್ ಹುಡುಕೋದು ಮತ್ತು ಪಾರ್ಸ್ ಮಾಡೋದು
        for line in lines:
            if 'price' in line.lower():
                # ಇದು 'price:1100', 'Price : 1100', 'PRICE  :  1100' ಎಲ್ಲವನ್ನೂ ಮ್ಯಾಚ್ ಮಾಡುತ್ತೆ
                match = re.search(r'price\s*:\s*(\d+)', line.lower())
                if match:
                    try:
                        input_price = int(match.group(1))
                    except Exception as e:
                        print("Price parse error:", e)

        # 🎯 2. ಜೀವನ್, ವಾಟ್ಸಾಪ್‌ಗೆ ಹೆಸರು ಫಿಕ್ಸ್ ಮಾಡೋ ಪಕ್ಕಾ ಬ್ರ್ಯಾಂಡಿಂಗ್ ಲಾಜಿಕ್:
        # ಮೊದಲನೇ ಲೈನ್ (Category) ಮತ್ತು 'price' ಇರೋ ಯಾವುದೇ ಲೈನ್ ಅನ್ನು ಹೆಸರಿಗೆ ತಗೋಬಾರದು.
        valid_name_lines = []
        for line in lines[1:]: # ಮೊದಲನೇ ಲೈನ್ ಬಿಟ್ಟು ಉಳಿದವೆಲ್ಲಾ
            if 'price' not in line.lower():
                valid_name_lines.append(line)
        
        # ಒಂದು ವೇಳೆ ನೀವು ಬಟ್ಟೆಯ ಹೆಸರು ಕೊಟ್ಟಿದ್ರೆ ಅದನ್ನೇ ತಗೊಳ್ಳುತ್ತೆ, ಇಲ್ಲಾಂದ್ರೆ 'Premium [Category Name]' ಅಂತ ತಗೊಳ್ಳುತ್ತೆ
        if valid_name_lines:
            name = " ".join(valid_name_lines)
        else:
            name = "Premium " + category

        # ಒಂದು ವೇಳೆ ನೀವು ಬೋಟ್‌ನಲ್ಲಿ ಪ್ರೈಸ್ ಕಳಿಸದಿದ್ದರೆ, ಡಿಫಾಲ್ಟ್ ಲಿಸ್ಟ್‌ನಿಂದ ತಗೊಳ್ಳುತ್ತೆ
        if input_price is None:
            cat_lower = category.lower().strip()
            input_price = DEFAULT_PRICES.get(cat_lower, 0)

        # 40% ಆಟೋಮ್ಯಾಟಿಕ್ ಮಾರ್ಕಪ್ ಕ್ಯಾಲ್ಕುಲೇಷನ್ (ವೆಬ್‌ಸೈಟ್‌ಗೆ ಮಾತ್ರ)
        calculated_original = int(input_price * 1.40)
        
        price = str(input_price)
        original_price = str(calculated_original)

        # Download image from Telegram
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile", params={"file_id": file_id}).json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        downloaded_photo = requests.get(file_url).content

        description = f"Premium {name} from Dolphin Trends"
        final_product_image_bytes = None

        # ================== AI EDIT MODE ==================
        if is_edit_requested:
            send_telegram(chat_id, "🤖 AI Edit mode active. Generating model image...")
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                import base64
                image_base64 = base64.b64encode(downloaded_photo).decode("utf-8")
                
                gemini_payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Analyze the dress. Give me a short 20-word description of its exact color, pattern, and style. No extra text."},
                            {"inlineData": {"mimeType": "image/jpeg", "data": image_base64}}
                        ]
                    }]
                }
                gemini_res = requests.post(gemini_url, json=gemini_payload, timeout=30).json()
                try:
                    dress_details = gemini_res['candidates'][0]['content']['parts'][0]['text'].strip()
                except:
                    dress_details = "traditional Indian dress"

                ai_prompt = (
                    f"A single high-resolution product catalog image showcasing a beautiful young Indian fashion model in TWO different stylish poses within the SAME frame side-by-side. "
                    f"Full body shot visible from head to toe. She is wearing the exact outfit: {dress_details}. "
                    f"The background is a clean, professional studio white backdrop featuring a beautiful watercolor splash with a blue dolphin logo and the text 'DOLPHIN TRENDS' printed clearly in the center behind the model."
                )
                
                encoded_prompt = urllib.parse.quote(ai_prompt)
                pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&model=flux"
                
                img_response = requests.get(pollinations_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                if img_response.status_code == 200 and len(img_response.content) > 1000:
                    final_product_image_bytes = img_response.content 
                else:
                    send_telegram(chat_id, "⚠️ AI busy, falling back to original photo.")
            except Exception as e:
                print("AI Error:", str(e))
                send_telegram(chat_id, "⚠️ AI error, using original photo.")

        else:
            send_telegram(chat_id, "⚡ Direct upload mode active (No AI changes).")

        # ================== SAVE & UPLOAD ==================
        send_telegram(chat_id, "🚀 Saving and uploading image...")
        filename = str(uuid.uuid4()) + ".jpg"
        filepath = f"uploads/{filename}"
        
        if final_product_image_bytes:
            img_file = io.BytesIO(final_product_image_bytes)
        else:
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

        send_telegram(chat_id, f"✅ Product Active!\n🌐 Website uploaded with Price: Rs.{price}\n📲 WhatsApp shared (No Price!)\n🌐 {FRONTEND_URL}")

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
