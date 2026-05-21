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
import base64
import io
import google.generativeai as genai

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

genai.configure(api_key=GEMINI_API_KEY)

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

def send_whatsapp(image_url, name, price):
    try:
        caption = f"🔥 *Hurry! Limited Stock!*\n\n✨ {name}\n\n💃 *Grab yours before it's gone!*\n\n👇 *Shop Now:*\n{FRONTEND_URL}"
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": WHATSAPP_NUMBER,
            "urlFile": image_url,
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
        print("Update received:", json.dumps(update)[:200])

        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return {"ok": True}

        # Start command
        if "text" in message and message["text"] == "/start":
            send_telegram(chat_id,
                "✅ Dolphin Trends Bot Ready!\n\n"
                "📸 Product photo kalsidre auto upload aagthade\n\n"
                "⚡ Direct mode: photo + caption alli #direct bari\n"
                "Example: Blue Kurti #direct"
            )
            return {"ok": True}

        # Photo handler
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

        # Download image
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile",
            params={"file_id": file_id}
        ).json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        image_bytes = requests.get(file_url).content

        final_image = image_bytes
        name = "Dolphin Fashion"
        category = "Sets"
        description = "Premium fashion collection from Dolphin Trends"

        # Direct mode
        if is_direct:
            send_telegram(chat_id, "⚡ Direct upload mode!")
            clean_caption = caption.replace("#direct","").strip()
            for part in ["Price:", "Original:", "price:", "original:"]:
                clean_caption = clean_caption.split(part)[0].strip()
            if clean_caption:
                name = clean_caption

        # AI mode
        else:
            send_telegram(chat_id, "🤖 AI analyzing image...")
            try:
                from google import genai as genai2
                client = genai2.Client(api_key=GEMINI_API_KEY)
                from PIL import Image as PILImage
                image_pil = PILImage.open(io.BytesIO(image_bytes))
                prompt = 'Analyze this clothing photo. Respond ONLY in JSON: {"name":"product name","category":"Sets","description":"short description","dress_details":"dress color and style"}'
                response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt, image_pil])
                response_text = response.text.strip()
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                ai_data = json.loads(response_text)
                name = ai_data.get("name","Fashion Item")
                category = ai_data.get("category","Sets")
                description = ai_data.get("description","Beautiful fashion item")
                dress_details = clean_text(ai_data.get("dress_details","beautiful traditional dress"))

                send_telegram(chat_id, "🎨 Generating AI model image...")
                ai_prompt = requests.utils.quote(f"beautiful young Indian woman wearing {dress_details}, white background, studio photography")
                pollinations_url = f"https://image.pollinations.ai/prompt/{ai_prompt}?width=768&height=1024&seed=42&nologo=true&model=flux"
                img_response = requests.get(pollinations_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=60)
                if img_response.status_code == 200 and len(img_response.content) > 1000:
                    final_image = img_response.content
            except Exception as e:
                print("AI Error:", e)

        # Upload to website
        send_telegram(chat_id, "🚀 Uploading to website...")
        ext = "jpg"
        filename = str(uuid.uuid4()) + "." + ext
        filepath = f"uploads/{filename}"
        with open(filepath, "wb") as f:
            f.write(final_image)

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

        # Send WhatsApp
        wa_success = send_whatsapp(product["image"], name, "Rs." + price)

        if wa_success:
            send_telegram(chat_id,
                f"✅ Upload successful!\n📲 WhatsApp sent!\n\n"
                f"🛍️ {name}\n💰 Rs.{price}\n📂 {category}\n\n🌐 {FRONTEND_URL}"
            )
        else:
            send_telegram(chat_id,
                f"✅ Website upload done!\n⚠️ WhatsApp failed\n\n"
                f"🛍️ {name}\n💰 Rs.{price}\n🌐 {FRONTEND_URL}"
            )

        return {"ok": True}

    except Exception as e:
        print("Webhook Error:", str(e))
        return {"ok": True}

# ================= PRODUCTS =================

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
        "image": "https://dolphin-trends-3.onrender.com/uploads/" + filename,
        "available": True
    }
    products_table.insert(product)
    return product

@app.post("/upload-from-bot")
async def upload_from_bot(
    file: UploadFile = File(...), name: str = Form(...),
    price: str = Form(...), original_price: str = Form(...),
    description: str = Form(...), category: str = Form(...)
):
    try:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = str(uuid.uuid4()) + "." + ext
        filepath = f"uploads/{filename}"
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        product = {
            "id": str(uuid.uuid4()), "name": name, "price": price,
            "original_price": original_price, "description": description,
            "category": category,
            "image": "https://dolphin-trends-3.onrender.com/uploads/" + filename,
            "available": True
        }
        products_table.insert(product)
        return {"success": True, "product": product}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/products/{product_id}")
def update_product(product_id: str, data: ProductUpdate):
    Product = Query()
    existing = products_table.search(Product.id == product_id)
    if not existing:
        return {"error": "Product not found"}
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    products_table.update(update_data, Product.id == product_id)
    updated = products_table.search(Product.id == product_id)
    return updated[0] if updated else {}

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
            filepath = "uploads/" + filename
            if os.path.exists(filepath):
                os.remove(filepath)
    except:
        pass
    products_table.remove(Product.id == product_id)
    return {"success": True, "message": "Product deleted"}

@app.put("/products/{product_id}/availability")
def update_availability(product_id: str, available: bool):
    Product = Query()
    products_table.update({"available": available}, Product.id == product_id)
    product = products_table.search(Product.id == product_id)
    return product[0] if product else {}

# ================= REVIEWS =================

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    Review = Query()
    return reviews_table.search(Review.product_id == product_id)

@app.post("/reviews")
def add_review(review: dict):
    review["id"] = str(uuid.uuid4())
    reviews_table.insert(review)
    return review

# ================= BOOKINGS =================

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

# ================= AI MODEL IMAGE =================

@app.post("/generate-model-image")
async def generate_model_image(file: UploadFile = File(...)):
    try:
        API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-3.5-large/text-to-image"
        headers = {"Authorization": "Bearer " + HF_TOKEN}
        payload = {"inputs": "A beautiful young Indian woman wearing elegant fashion dress, studio white background, professional photography"}
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            gen_filename = str(uuid.uuid4()) + ".png"
            gen_filepath = "uploads/" + gen_filename
            with open(gen_filepath, "wb") as f:
                f.write(response.content)
            return {"success": True, "image_url": "https://dolphin-trends-3.onrender.com/uploads/" + gen_filename}
        else:
            return {"success": False, "error": "HF API error " + str(response.status_code)}
    except Exception as e:
        return {"success": False, "error": str(e)}
