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

# ================= MODELS =================

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[str] = None
    original_price: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    available: Optional[bool] = None

# ================= HELPERS =================

def send_telegram(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def send_whatsapp(image_url, name, final_price, final_original):
    try:
        caption = (
            f"🔥 *Hurry! Limited Stock!*\n\n"
            f"✨ *Dolphin Collections: {name}*\n"
            f"💰 *Price:* Rs.{final_price}  (❌ MRP: ~Rs.{final_original}~)\n"
            f"💃 *Grab yours before it's gone!*\n\n"
            f"👇 *Shop Now:*\n{FRONTEND_URL}"
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
    return {"status": "Dolphin Trends Backend with Dynamic Categories Active"}

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

        # 🎯 1. ಲೈನ್ ಬೈ ಲೈನ್ ಪಾರ್ಸಿಂಗ್ ಲಾಜಿಕ್
        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        
        # ಡಿಫಾಲ್ಟ್ ವ್ಯಾಲ್ಯೂಗಳು
        category = "Kurta Sets"
        name = "Premium Collection"
        input_price = 499

        # ಜೀವನ್, ನೀವು ಕಳಿಸೋ ಮೆಸೇಜ್‌ನಿಂದ ಡೇಟಾ ತಗೆದುಕೊಳ್ಳುವ ಪರ್ಫೆಕ್ಟ್ ಲಾಜಿಕ್:
        if len(lines) > 0:
            # ಮೊದಲನೇ ಲೈನ್ ಅನ್ನು ಯಥಾವತ್ತಾಗಿ ಕ್ಯಾಟಗರಿ ಹೆಸರು ಅಂತ ತಗೋತ್ತೆ (ಉದಾ: Leggings, Umbrella Sets)
            category = lines[0].replace("#edit", "").strip()
        
        if len(lines) > 1 and not lines[1].lower().startswith('price:'):
            # ಎರಡನೇ ಲೈನ್ ಬಟ್ಟೆಯ ಹೆಸರು
            name = lines[1]
        else:
            name = "Premium " + category

        # ಪ್ರೈಸ್ ಪಾರ್ಸಿಂಗ್ ಮತ್ತು ಆಟೋ 40% ಕ್ಯಾಲ್ಕುಲೇಷನ್
        for line in lines:
            if 'price:' in line.lower():
                try:
                    price_str = line.split(':')[1].strip().replace("₹","").replace("Rs.","").strip()
                    input_price = int(price_str)
                except Exception as e:
                    print("Price parse error:", e)

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

        # Database insert (ನಿಮ್ಮ ವೆಬ್‌ಸೈಟ್ ಮ್ಯಾಚಿಂಗ್ ಕ್ಯಾಟಗರಿ ಇಲ್ಲಿ ಸೇವ್ ಆಗುತ್ತೆ ಜೀವನ್)
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
        wa_success = send_whatsapp(product["image"], name, price, original_price)

        if wa_success:
            send_telegram(chat_id, f"✅ Uploaded to category: {category}!\n🌐 Website & 📲 WhatsApp Active!\n\n🛍️ {name}\n💰 Price: Rs.{price} (MRP: Rs.{original_price})\n🌐 {FRONTEND_URL}")
        else:
            send_telegram(chat_id, f"✅ Website uploaded to {category}!\n⚠️ WhatsApp failed.\n\n🛍️ {name}\n🌐 {FRONTEND_URL}")

        return {"ok": True}
    except Exception as e:
        print("Error:", str(e))
        return {"ok": True}

# ================= PRODUCTS ENDPOINTS =================

@app.get("/products")
def get_products():
    return products_table.all()

@app.post("/products")
async def add_product(
    name: str = Form(...), price: str = Form(...),
    original_price: str = Form(...), description: str = Form(...),
    category: str = Form(...), file: UploadFile = File(...)
):
    ext = file.filename.split(".")[-1]
    filename = str(uuid.uuid4()) + "." + ext
    filepath = "uploads/" + filename
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    product = {
        "id": str(uuid.uuid4()), "name": name, "price": price,
        "original_price": original_price, "description": description,
        "category": category, "image": f"{BACKEND_URL}/uploads/{filename}", "available": True
    }
    products_table.insert(product)
    return product

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

# ================= REVIEWS & BOOKINGS =================

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    Review = Query()
    return reviews_table.search(Review.product_id == product_id)

@app.post("/reviews")
def add_review(review: dict):
    review["id"] = str(uuid.uuid4())
    reviews_table.insert(review)
    return review

@app.post("/bookings")
def add_booking(booking: dict):
    booking["id"] = str(uuid.uuid4())
    booking["status"] = "Pending"
    bookings_table.insert(booking)
    return booking

@app.get("/bookings")
def get_bookings():
    return bookings_table.all()
