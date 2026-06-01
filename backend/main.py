import os
import io
import uuid
import time
import requests
import re
from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
import cloudinary
import cloudinary.uploader

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ENV =================
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "https://dolphin-trends-3.onrender.com"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY_VAL = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY_VAL,
    api_secret=CLOUDINARY_API_SECRET
)

JEEVAN_TELEGRAM_CHAT_ID = 2113728041
YOUR_PERSONAL_PHONE = "917411255628"

# ================= MONGODB =================
ca = certifi.where()
db = None
bookings_table = None
products_table = None

if MONGO_URL:
    try:
        client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
        db = client["dolphin_trends_db"]
        products_table = db["products"]
        bookings_table = db["bookings"]
        print("✅ MongoDB Connected!")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

# ================= STARTUP WEBHOOK =================
@app.on_event("startup")
async def startup():
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook", timeout=5)
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": f"{BACKEND_URL}/webhook"},
                timeout=5
            )
            print("Webhook set:", r.text)
        except Exception as e:
            print("Webhook error:", e)

# ================= CLOUDINARY UPLOAD =================
def upload_to_cloudinary(image_source, is_file=False):
    try:
        if not CLOUDINARY_CLOUD_NAME or CLOUDINARY_CLOUD_NAME == "":
            print("⚠️ Cloudinary not configured!")
            return None
        result = cloudinary.uploader.upload(
            image_source,
            folder="dolphin_trends",
            resource_type="image",
            timeout=30
        )
        url = result.get("secure_url")
        print(f"✅ Cloudinary upload success: {url}")
        return url
    except Exception as e:
        print(f"❌ Cloudinary Upload Error: {str(e)}")
        return None

# ================= WHATSAPP =================
def send_whatsapp_image(image_url, product_name):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
            return False
        caption = (
            f"🔥 *New Arrival at Dolphin Trends!* 🐬\n\n"
            f"👗 *Product:* {product_name}\n"
            f"💃 Grab yours before it's gone!\n\n"
            f"💥 *Explore & order here:* 👇\n"
            f"🔗 {FRONTEND_URL}"
        )
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": f"{YOUR_PERSONAL_PHONE}@c.us",
            "urlFile": image_url,
            "fileName": f"{product_name.replace(' ', '_')}.jpg",
            "caption": caption
        }
        response = requests.post(url, json=payload, timeout=30)
        print("WhatsApp Status:", response.status_code)
        return response.status_code == 200
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

def send_whatsapp_msg(phone, message):
    try:
        if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
            return False
        phone = str(phone).replace("+", "").replace(" ", "").strip()
        if len(phone) == 10:
            phone = f"91{phone}"
        chat_id = f"{phone}@c.us"
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        requests.post(url, json={"chatId": chat_id, "message": message}, timeout=5)
        return True
    except:
        return False

# ================= AI =================
def generate_product_details_via_ai(image_url):
    try:
        if not GOOGLE_API_KEY:
            return "Premium Dress", "Suit Set", "Curated boutique wear."
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        response = requests.get(image_url, timeout=10)
        image_bytes = response.content
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        prompt = (
            "Analyze this boutique fashion clothing image. "
            "1. Provide a simple product name. "
            "2. Category (one or two words). "
            "3. Short attractive description (1-2 sentences). "
            "Format: Name | Category | Description"
        )
        cookie_img = {"mime_type": "image/jpeg", "data": image_bytes}
        ai_response = model.generate_content([prompt, cookie_img])
        text_res = ai_response.text.strip()
        if "|" in text_res:
            parts = text_res.split("|")
            return parts[0].strip(), parts[1].strip(), parts[2].strip() if len(parts) > 2 else "Beautiful outfit."
        return "Premium Dress", "Suit Set", "Beautiful design crafted with rich fabric."
    except Exception as e:
        print("AI Error:", e)
        return "Premium Dress", "Suit Set", "Beautiful design crafted with rich fabric."

# ================= MODELS =================
class BookingPayload(BaseModel):
    customer_name: str
    customer_phone: str
    product_name: str
    image_url: str
    size: str = "M"
    price: str = "₹1299"

# ================= HEALTH =================
@app.get("/")
def home():
    return {"status": "Dolphin Trends Backend Active!"}

# ================= BOOKING =================
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
        admin_message = (
            f"🛍️ *New Buy Request!*\n\n"
            f"👗 *Product:* {payload.product_name}\n"
            f"📏 Size: {payload.size}\n"
            f"💰 Price: {payload.price}\n"
            f"👤 Name: {payload.customer_name}\n"
            f"📞 Phone: {payload.customer_phone}\n\n"
            f"⚙️ Admin Panel: {FRONTEND_URL}"
        )
        send_whatsapp_msg(YOUR_PERSONAL_PHONE, admin_message)
        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= ADD PRODUCT (FIXED) =================
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

        # ✅ File upload ಮಾಡಿ Cloudinary ಗೆ
        if file and file.filename and file.filename != "":
            file_bytes = await file.read()
            if file_bytes and len(file_bytes) > 100:
                print(f"📸 Uploading image: {file.filename} ({len(file_bytes)} bytes)")
                cloud_image_url = upload_to_cloudinary(file_bytes, is_file=True)
                if cloud_image_url:
                    print(f"✅ Image URL: {cloud_image_url}")
                else:
                    print("❌ Cloudinary failed!")
                    raise HTTPException(status_code=500, detail="Image upload to Cloudinary failed! Check Cloudinary credentials.")
            else:
                raise HTTPException(status_code=400, detail="Empty file uploaded!")
        else:
            raise HTTPException(status_code=400, detail="Please upload a product image!")

        # ✅ Always new product — no duplicate name check
        new_id = str(uuid.uuid4())[:8]
        product_data = {
            "id": new_id,
            "product_id": new_id,
            "name": name,
            "price": price,
            "original_price": original_price or "",
            "category": category,
            "description": description or "",
            "image": cloud_image_url,
            "available": is_available
        }
        products_table.insert_one(product_data)
        print(f"✅ Product saved: {name}")
        return {"status": "success", "action": "created", "product_id": new_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Add product error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================= UPDATE PRODUCT =================
@app.put("/api/products/{product_id}")
@app.put("/products/{product_id}")
def update_product(product_id: str, payload: dict):
    if not product_id or product_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid ID")
    if products_table is None:
        raise HTTPException(status_code=500, detail="DB missing")
    result = products_table.update_one(
        {"$or": [{"product_id": product_id}, {"id": product_id}]},
        {"$set": payload}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "success"}

# ================= DELETE PRODUCT =================
@app.delete("/api/products/{product_id}")
@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    if not product_id or product_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid ID")
    if products_table is None:
        raise HTTPException(status_code=500, detail="DB missing")
    products_table.delete_one({"$or": [{"product_id": product_id}, {"id": product_id}]})
    return {"success": True}

# ================= PRODUCTS GET =================
@app.get("/products")
def get_products():
    if products_table is None:
        return []
    return list(products_table.find({}, {"_id": 0}))

# ================= REVIEWS =================
@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    if db is None or not product_id or product_id == "undefined":
        return []
    return list(db["reviews"].find({"product_id": product_id}, {"_id": 0}))

@app.post("/reviews")
def add_review(review: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="DB missing")
    review["id"] = str(uuid.uuid4())
    db["reviews"].insert_one(review)
    review.pop("_id", None)
    return review

# ================= BOOKINGS GET =================
@app.get("/api/admin/bookings")
@app.get("/bookings")
def get_bookings():
    if bookings_table is None:
        return []
    return list(bookings_table.find({}, {"_id": 0}))

# ================= DELETE BOOKING =================
@app.delete("/api/admin/bookings/{booking_id}")
@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    if not booking_id or booking_id == "undefined":
        raise HTTPException(status_code=400, detail="Invalid Booking ID")
    if bookings_table is None:
        raise HTTPException(status_code=500, detail="DB missing")
    result = bookings_table.delete_one({"booking_id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"success": True}

# ================= UPDATE BOOKING =================
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
                f"Good news! *{p_name}* is available at Dolphin Trends!\n\n"
                f"🏪 *Store Address:*\n"
                f"Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore\n"
                f"📍 Map: https://maps.app.goo.gl/amrkmppGsdgprtx27\n"
                f"⏰ Timings: 11:00 AM - 10:00 PM\n\n"
                f"See you soon! 🛍️\nTeam Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Approved"}})

        elif action == "disagree":
            msg = (
                f"Hello {c_name},\n\n"
                f"Sorry, *{p_name}* is currently out of stock.\n"
                f"We'll notify you when it's back!\n\nTeam Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Out of Stock"}})

        elif action == "size_unavail":
            msg = (
                f"Hello {c_name}! 😊\n\n"
                f"*{p_name}* is available but your size is out of stock.\n"
                f"Please visit our store!\n"
                f"📍 Peenya 2nd Stage, Bangalore\nTeam Dolphin Trends 🐬"
            )
            send_whatsapp_msg(c_phone, msg)
            bookings_table.update_one({"booking_id": booking_id}, {"$set": {"status": "Size Unavailable"}})

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= TELEGRAM WEBHOOK =================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if products_table is None:
        return {"status": "DB error"}
    try:
        data = await request.json()
        if "message" not in data:
            return {"status": "ok"}

        message = data["message"]
        chat_id = message["chat"]["id"]

        if chat_id != JEEVAN_TELEGRAM_CHAT_ID:
            return {"status": "Ignored"}

        if "photo" not in message:
            return {"status": "ok"}

        caption = message.get("caption", "").strip()
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=10
        ).json()
        file_path = file_info.get("result", {}).get("file_path")

        if not file_path:
            return {"status": "ok"}

        telegram_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        permanent_url = upload_to_cloudinary(telegram_image_url)
        if not permanent_url:
            permanent_url = telegram_image_url

        product_name = "Premium Dress"
        product_price = "₹1500"
        product_category = "Suit Set"
        product_description = "Curated boutique wear."

        if caption:
            clean_caption = caption.replace("#edit", "").strip()
            lines = [l.strip() for l in clean_caption.split("\n") if l.strip()]
            clean_text = " ".join(lines)
            price_match = re.search(r'(?:₹\s*)?(\d{3,5})', clean_text)

            if "-" in clean_caption:
                parts = clean_caption.split("-")
                if len(parts) >= 3:
                    product_name = parts[0].strip()
                    product_price = parts[1].strip()
                    product_category = parts[2].strip()
            elif price_match:
                product_price = f"₹{price_match.group(1)}"
                product_name = clean_text.replace(price_match.group(0), "").replace("₹", "").strip() or product_name

        if not caption or product_name == "Premium Dress":
            ai_name, ai_cat, ai_desc = generate_product_details_via_ai(permanent_url)
            product_name = ai_name
            product_category = ai_cat
            product_description = ai_desc

        new_id = str(uuid.uuid4())[:8]
        products_table.insert_one({
            "product_id": new_id, "id": new_id,
            "name": product_name, "price": product_price,
            "category": product_category, "image": permanent_url,
            "description": product_description, "available": True
        })

        send_whatsapp_image(permanent_url, product_name)
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": f"✅ Uploaded!\n• Name: {product_name}\n• Price: {product_price}\n• Category: {product_category}\n📲 WhatsApp sent!"
            },
            timeout=5
        )

        return {"status": "success"}
    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return {"status": "error"}
