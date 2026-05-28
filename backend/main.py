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
import google.generativeai as genai  # 🧠 Google Gemini SDK

# ☁️ Cloudinary Libraries
import cloudinary
import cloudinary.uploader

app = FastAPI()

# CORS Setting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ⚙️ CONFIGURATION & CONNECTIONS ───
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ☁️ CLOUDINARY SETUP (Render Environment Variables ನಲ್ಲಿ ಇವುಗಳನ್ನು ಆಡ್ ಮಾಡಿ ಜೀವನ್)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME") or "YOUR_CLOUD_NAME"
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY") or "YOUR_API_KEY"
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET") or "YOUR_API_SECRET"

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# Google Gemini AI Setup
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 🤖 TELEGRAM BOT CONFIGURATION
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
JEEVAN_TELEGRAM_CHAT_ID = 2113728041
YOUR_PERSONAL_PHONE = "917411255628"
YOUR_UPI_ID = "7411255628@ybl"  

ca = certifi.where()
db = None
bookings_table = None
products_table = None

if MONGO_URL:
    client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=2000, serverSelectionTimeoutMS=2000)
    db = client["dolphin_trends_db"]
    products_table = db["products"]
    bookings_table = db["bookings"]

# Helper: Cloudinary ಇಮೇಜ್ ಅಪ್‌ಲೋಡರ್ ಫಂಕ್ಷನ್
def upload_to_cloudinary(image_source, is_file=False):
    try:
        if is_file:
            # ಅಡ್ಮಿನ್ ಪ್ಯಾನಲ್‌ನಿಂದ ಬರುವ ಫೈಲ್ ಅಪ್‌ಲೋಡ್
            result = cloudinary.uploader.upload(image_source, folder="dolphin_trends")
        else:
            # ಟೆಲಿಗ್ರಾಮ್ ಯುಆರ್‌ಎಲ್ ಮೂಲಕ ಅಪ್‌ಲೋಡ್
            result = cloudinary.uploader.upload_image(image_source, folder="dolphin_trends")
        return result.get("secure_url")
    except Exception as e:
        print(f"❌ Cloudinary Upload Error: {str(e)}")
        # ಫೇಲ್ ಆದ್ರೆ ಟೆಂಪರರಿ ಒಂದು ಸುಂದರವಾದ ಇಮೇಜ್ ಲಿಂಕ್ ರಿಟರ್ನ್ ಮಾಡುತ್ತೆ
        return "https://images.unsplash.com/photo-1618932260643-eee4a2f652a6?q=80&w=500"

# ─── 📨 WHATSAPP MESSAGE FUNCTION ───
def send_whatsapp(phone, message):
    if not GREEN_API_INSTANCE or not GREEN_API_TOKEN:
        return False
    phone = str(phone).replace("+", "").replace(" ", "").strip()
    if len(phone) == 10:
        phone = f"91{phone}"
    chat_id = f"{phone}@c.us"
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
    try:
        requests.post(url, json={"chatId": chat_id, "message": message}, timeout=5)
        return True
    except:
        return False

# ─── 🧠 SMART GEMINI AI FUNCTION ───
def generate_product_details_via_ai(image_url):
    try:
        if not GOOGLE_API_KEY:
            return "Dolphin Trends Premium Suit", "Suit Set", "Exclusively curated premium collection."
        response = requests.get(image_url)
        image_bytes = response.content
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (
            "Analyze this boutique fashion clothing image for Dolphin Trends. "
            "1. Provide a beautiful simple product name. "
            "2. Identify the category in one or two words maximum. "
            "3. Provide a short, attractive boutique description (1-2 sentences). "
            "Format: Name | Category | Description"
        )
        cookie_img = {"mime_type": "image/jpeg", "data": image_bytes}
        ai_response = model.generate_content([prompt, cookie_img])
        text_res = ai_response.text.strip()
        if "|" in text_res:
            parts = text_res.split("|")
            return parts[0].strip(), parts[1].strip(), parts[2].strip()
        return "Dolphin Trends Premium Suit", "Uncategorized", "Premium quality outfit."
    except:
        return "Dolphin Trends Premium Suit", "Suit Set", "Beautiful design crafted with rich fabric."

class BookingPayload(BaseModel):
    customer_name: str
    customer_phone: str
    product_name: str
    image_url: str
    size: str = "M"
    price: str = "₹1299"

# ─── 🚀 1. CUSTOMER BOOKING API ───
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
        
        admin_message = f"🛍️ *New Buy Request!*\n\n👗 *Product:* {payload.product_name}\n📏 Size: {payload.size}\n💰 Price: {payload.price}\n👤 Name: {payload.customer_name}\n📞 Phone: {payload.customer_phone}"
        send_whatsapp(YOUR_PERSONAL_PHONE, admin_message)
        return {"status": "success", "booking_id": booking_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── 🛍️ 2. ADMIN PANEL UPLOAD (ಪರ್ಮನೆಂಟ್ ಕ್ಲೌಡ್ ಅಪ್‌ಲೋಡ್ ಫಿಕ್ಸ್) ───
@app.post("/products")
async def add_or_update_product_via_panel(
    name: str = Form(...),
    price: str = Form(...),
    original_price: str = Form(None),
    description: str = Form(None),
    category: str = Form(...),
    file: UploadFile = File(None)
):
    if products_table is None:
        raise HTTPException(status_code=500, detail="Database missing")
    try:
        existing_product = products_table.find_one({"name": name})
        
        # ಫೋಟೋ ಬಂದರೆ Cloudinary ಗೆ ಅಪ್‌ಲೋಡ್ ಮಾಡು
        cloud_image_url = None
        if file:
            file_bytes = await file.read()
            cloud_image_url = upload_to_cloudinary(file_bytes, is_file=True)

        if existing_product:
            update_data = {
                "price": price,
                "category": category,
                "description": description or ""
            }
            if original_price:
                update_data["original_price"] = original_price
            if cloud_image_url:
                update_data["image"] = cloud_image_url

            products_table.update_one({"name": name}, {"$set": update_data})
            return {"status": "success", "action": "updated", "product_id": existing_product["product_id"]}
        else:
            # ಹೊಸ ಪ್ರಾಡಕ್ಟ್‌ಗೆ ಫೋಟೋ ಇಲ್ಲದಿದ್ದರೆ ಡಿಫಾಲ್ಟ್ ಬ್ಯಾಕಪ್ ಇಮೇಜ್
            final_image = cloud_image_url if cloud_image_url else "https://images.unsplash.com/photo-1618932260643-eee4a2f652a6?q=80&w=500"
            new_id = str(uuid.uuid4())[:6]
            product_data = {
                "product_id": new_id,
                "name": name,
                "price": price,
                "original_price": original_price or "",
                "category": category,
                "description": description or "",
                "image": final_image
            }
            products_table.insert_one(product_data)
            return {"status": "success", "action": "created", "product_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── 🤖 3. TELEGRAM BOT WEBHOOK (ಪರ್ಮನೆಂಟ್ ಇಮೇಜ್ ಹೋಸ್ಟಿಂಗ್ ಫಿಕ್ಸ್) ───
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if products_table is None: return {"status": "DB error"}
    try:
        data = await request.json()
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            if chat_id != JEEVAN_TELEGRAM_CHAT_ID: return {"status": "Ignored"}

            if "photo" in message:
                caption = message.get("caption", "").strip()
                file_id = message["photo"][-1]["file_id"]
                file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}").json()
                file_path = file_info.get("result", {}).get("file_path")

                if file_path:
                    telegram_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                    
                    # 🔥 ಕ್ರಾಶ್ ತಡೆಯುವ ಪ್ರಮುಖ ಬದಲಾವಣೆ: ಮೊದಲು ಟೆಲಿಗ್ರಾಮ್ ಫೋಟೋವನ್ನು Cloudinary ಗೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಪರ್ಮನೆಂಟ್ ಲಿಂಕ್ ಪಡಿಯಿರಿ
                    permanent_cloud_url = upload_to_cloudinary(telegram_image_url, is_file=False)

                    product_name, product_price, product_category, product_description = "Premium Dress", "₹1500", "Suit Set", "Curated boutique wear."
                    
                    if caption:
                        lines = [l.strip() for l in caption.split("\n") if l.strip()]
                        clean_text = " ".join(lines)
                        price_match = re.search(r'(?:₹\s*)?(\d{3,5})', clean_text)
                        
                        if "-" in caption:
                            parts = caption.split("-")
                            if len(parts) >= 3:
                                product_name, product_price, product_category = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        elif price_match:
                            product_price = f"₹{price_match.group(1)}"
                            product_name = clean_text.replace(price_match.group(0), "").replace("₹", "").strip() or product_name
                    
                    # AI ವಿವರಣೆ ಜನರೇಷನ್
                    _, ai_cat, ai_desc = generate_product_details_via_ai(permanent_cloud_url)
                    if "Premium Dress" in product_name or not caption:
                        product_name, product_category, product_description = generate_product_details_via_ai(permanent_cloud_url)

                    # ಡೇಟಾಬೇಸ್‌ಗೆ ಸೇವ್ (Cloudinary ಲಿಂಕ್‌ನೊಂದಿಗೆ)
                    new_id = str(uuid.uuid4())[:6]
                    products_table.insert_one({
                        "product_id": new_id, "name": product_name, "price": product_price,
                        "category": product_category, "image": permanent_cloud_url, "description": product_description
                    })

                    # Telegram Reply
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
                        "chat_id": chat_id, "text": f"✅ Uploaded to Cloudinary & Website!\n• Name: {product_name}\n• Price: {product_price}"
                    })
        return {"status": "success"}
    except Exception as e:
        print(f"Master Webhook Error: {str(e)}")
        return {"status": "error"}

# ─── 🟢 🔴 🔵 4. OTHERS CONTROLLERS (SAFEGUARDED) ───
@app.put("/api/products/{product_id}")
@app.put("/products/{product_id}")
def update_product_direct(product_id: str, payload: dict):
    if not product_id or product_id == "undefined": raise HTTPException(status_code=400, detail="Invalid ID")
    products_table.update_one({"$or": [{"product_id": product_id}, {"id": product_id}]}, {"$set": payload})
    return {"status": "success"}

@app.delete("/api/products/{product_id}")
@app.delete("/products/{product_id}")
def delete_product_direct(product_id: str):
    if not product_id or product_id == "undefined": raise HTTPException(status_code=400, detail="Invalid ID")
    products_table.delete_one({"$or": [{"product_id": product_id}, {"id": product_id}]})
    return {"success": True}

@app.get("/products")
def get_products():
    return list(products_table.find({}, {"_id": 0})) if products_table is not None else []

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    if db is None or not product_id or product_id == "undefined": return []
    return list(db["reviews"].find({"product_id": product_id}, {"_id": 0}))

@app.post("/reviews")
def add_review(review: dict):
    db["reviews"].insert_one(review)
    review.pop("_id", None)
    return review

@app.get("/api/admin/bookings")
@app.get("/bookings")
def get_bookings():
    return list(bookings_table.find({}, {"_id": 0})) if bookings_table is not None else []

@app.get("/")
def home(): return {"status": "Dolphin Trends Cloudinary Secure Backend Active!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
