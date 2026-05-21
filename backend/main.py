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

HF_TOKEN = os.environ.get("HF_TOKEN", "")
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

def clean_text(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\S+', '', text)
    text = text.replace("[","").replace("]","").replace("(","").replace(")","")
    return text.strip()

def send_telegram(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def send_whatsapp(image_url, name):
    try:
        caption = f"🔥 *Hurry! Limited Stock!*\n\n✨ *Dolphin Collections*\n\n💃 *Grab yours before it's gone!*\n\n👇 *Shop Now:*\n{FRONTEND_URL}"
        
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": WHATSAPP_NUMBER,
            "urlFile": image_url, # ವೆಬ್‌ಸೈಟ್‌ಗೆ ಅಪ್‌ಲೋಡ್ ಆದ ಅದೇ AI ಇಮೇಜ್ ಲಿಂಕ್ ವಾಟ್ಸಾಪ್‌ಗೆ ಹೋಗುತ್ತೆ
            "fileName": "product.jpg",
            "caption": caption
        }
        response = requests.post(url, json=payload, timeout=60)
        print("WhatsApp Status:", response.status_code, response.text)
        return response.status_code == 200
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= HEALTH =================

@app.get("/")
def home():
    return {"status": "Dolphin Trends Backend Running"}

# ================= WEBHOOK SETUP =================

@app.on_event("startup")
async def startup():
    webhook_url = f"{BACKEND_URL}/webhook"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
        json={"url": webhook_url}
    )
    print("Webhook set:", r.text)

# ================= TELEGRAM WEBHOOK =================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return {"ok": True}

        if "photo" not in message:
            return {"ok": True}

        send_telegram(chat_id, "📥 Photo received...")
        caption = message.get("caption", "")
        is_direct = "#direct" in caption.lower()

        # Price parse
        price = "499"
        original_price = "799"
        for line in caption.split('\n'):
            if 'price:' in line.lower():
                price = line.split(':')[1].strip().replace("₹","").replace("Rs.","").strip()
            if 'original:' in line.lower():
                original_price = line.split(':')[1].strip().replace("₹","").replace("Rs.","").strip()

        # Download image from Telegram
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile", params={"file_id": file_id}).json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        downloaded_photo = requests.get(file_url).content

        name = "Dolphin Fashion"
        category = "Sets"
        description = "Premium fashion collection from Dolphin Trends"
        
        final_product_image_bytes = None

        # ================== AI MODE (#direct ಇರಲ್ಲ) ==================
        if not is_direct:
            send_telegram(chat_id, "🤖 Analyzing dress with Gemini and generating model image...")
            try:
                # 1. Gemini AI ಮೂಲಕ ಫೋಟೋ ಅನಲೈಸ್ ಮಾಡಿ ಡೀಟೇಲ್ಸ್ ಪಡೆಯುವುದು
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                import base64
                image_base64 = base64.b64encode(downloaded_photo).decode("utf-8")
                
                gemini_payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Analyze the dress in this image. Give me only a short 20-word description of its exact color, pattern, fabric type, and embroidery details. Do not write anything else."},
                            {"inlineData": {"mimeType": "image/jpeg", "data": image_base64}}
                        ]
                    }]
                }
                gemini_res = requests.post(gemini_url, json=gemini_payload, timeout=30).json()
                
                try:
                    dress_details = gemini_res['candidates'][0]['content']['parts'][0]['text'].strip()
                    print("Gemini Analysis:", dress_details)
                except:
                    dress_details = "traditional Indian dress"
                    print("Gemini analysis failed, using default description")

                # 2. HuggingFace ಮೂಲಕ ಮಾದರಿ ಚಿತ್ರವನ್ನು ರಚಿಸುವುದು (ನಿಮ್ಮ ಹಳೇ API Key ಸಿಸ್ಟಮ್ ಜೀವನ್)
                hf_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                
                # ಒಂದೇ ಫ್ರೇಮ್‌ನಲ್ಲಿ ಎರಡು ಪೋಸ್ ಮತ್ತು Dolphin Trends ಲೋಗೋ ಬ್ಯಾಕ್‌ಗ್ರೌಂಡ್ ಇರೋ ಪ್ರಾಂಪ್ಟ್ ಸೆಟ್ ಮಾಡಿದ್ದೀನಿ
                ai_prompt = (
                    f"A single high-resolution product catalog image showcasing a beautiful young Indian fashion model in TWO different stylish poses within the SAME frame side-by-side. "
                    f"Full body shot visible from head to toe. She is wearing the exact outfit: {dress_details}. "
                    f"The background is a clean, professional studio white backdrop featuring a beautiful watercolor splash with a blue dolphin logo and the text 'DOLPHIN TRENDS' printed clearly in the center behind the model."
                )
                
                payload = {"inputs": ai_prompt}
                img_response = requests.post(hf_url, headers=headers, json=payload, timeout=90)
                
                if img_response.status_code == 200 and len(img_response.content) > 1000:
                    print("HuggingFace image received successfully")
                    final_product_image_bytes = img_response.content 
                else:
                    print(f"HF Error code: {img_response.status_code}")
                    send_telegram(chat_id, "⚠️ API Limit reached or busy, using original photo.")
            except Exception as e:
                print("AI Error:", str(e))
                send_telegram(chat_id, "⚠️ AI error, using original photo.")
                
        # ================== DIRECT MODE (#direct ಇರುತ್ತೆ) ==================
        else:
            send_telegram(chat_id, "⚡ Direct upload mode active.")
            lines = [line.strip() for line in caption.split('\n') if line.strip()]
            if len(lines) > 0:
                category_match = lines[0].replace("#direct", "").strip()
                if category_match:
                    category = category_match
            if len(lines) > 1 and not lines[1].lower().startswith(('price:', 'original:')):
                name = lines[1]
            else:
                name = "Premium " + category
                
        # ================== FILE PROCESSING & UPLOAD ==================
        send_telegram(chat_id, "🚀 Saving image and uploading everywhere...")
        filename = str(uuid.uuid4()) + ".jpg"
        filepath = f"uploads/{filename}"
        
        if final_product_image_bytes:
            img_file = io.BytesIO(final_product_image_bytes)
        else:
            img_file = io.BytesIO(downloaded_photo)
            
        try:
            image_pil = Image.open(img_file)
            if image_pil.mode in ("RGBA", "P"):
                image_pil = image_pil.convert("RGB")
            image_pil.save(filepath, "JPEG", quality=85, optimize=True)
        except Exception as e:
            print("Image save error:", str(e))
            send_telegram(chat_id, "⚠️ Image error, upload failed.")
            return {"ok": True}

        # ================== SAVE TO DATABASE ==================
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

        # ================== SEND TO WHATSAPP ==================
        wa_success = send_whatsapp(product["image"], name)

        if wa_success:
            send_telegram(chat_id,
                f"✅ AI Edit Successful!\n🌐 Website Uploaded!\n📲 WhatsApp Shared!\n\n"
                f"🛍️ {name}\n💰 Rs.{price}\n📂 {category}\n\n🌐 {FRONTEND_URL}"
            )
        else:
            send_telegram(chat_id, f"✅ Website upload done!\n⚠️ WhatsApp failed\n\n🛍️ {name}\n💰 Rs.{price}\n🌐 {FRONTEND_URL}")

        return {"ok": True}

    except Exception as e:
        print("Webhook Error:", str(e))
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
        "category": category,
        "image": f"{BACKEND_URL}/uploads/{filename}",
        "available": True
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
        print("Image delete error:", e)
        
    products_table.remove(Product.id == product_id)
    return {"success": True, "message": "Product deleted successfully"}

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

@app.put("/bookings/{booking_id}/confirm")
def confirm_booking(booking_id: str):
    Booking = Query()
    bookings_table.update({"status": "Confirmed"}, Booking.id == booking_id)
    booking = bookings_table.search(Booking.id == booking_id)
    return booking[0] if booking else {}

@app.put("/bookings/{booking_id}/reject")
def reject_booking(booking_id: str):
    Booking = Query()
    bookings_table.update({"status": "Rejected"}, Booking.id == booking_id)
    booking = bookings_table.search(Booking.id == booking_id)
    return booking[0] if booking else {}
