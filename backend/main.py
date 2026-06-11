import os
import uuid
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional
import certifi
import cloudinary
import cloudinary.uploader

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
products_col = None
bookings_col = None
reviews_col = None

if MONGO_URL:
    try:
        client = MongoClient(MONGO_URL, tlsCAFile=ca, connectTimeoutMS=10000, serverSelectionTimeoutMS=10000)
        db = client["dolphin_trends_db"]
        products_col = db["products"]
        bookings_col = db["bookings"]
        reviews_col  = db["reviews"]
        print("✅ MongoDB connected!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

# ================= HELPERS =================
def upload_to_cloudinary(image_source):
    try:
        result = cloudinary.uploader.upload(image_source, folder="dolphin_trends", resource_type="image")
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Error: {e}")
        return None

def doc_to_dict(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    if "product_id" not in doc:
        doc["product_id"] = doc["_id"]
    return doc

# ================= WHATSAPP =================
def send_whatsapp(image_url, name, description, price=""):
    try:
        caption = (
            "🛍️ *Dolphin Trends - New Arrival!*\n\n"
            f"👕 *Product:* {name}\n"
            f"📝 *Details:* {description}\n"
            f"💰 *Price:* {price}\n\n"
            f"🌐 *Shop Now:*\n{FRONTEND_URL}"
        )
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {
            "chatId": YOUR_WHATSAPP_GROUP_ID,
            "urlFile": image_url,
            "caption": caption
        }
        requests.post(url, json=payload, timeout=30)
        print("✅ WhatsApp sent!")
    except Exception as e:
        print(f"WhatsApp Error: {e}")

def send_telegram_reply(chat_id, text):
    """Telegram bot ಗೆ reply ಕಳಿಸು"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram reply error: {e}")

def send_whatsapp_notification(customer_phone, customer_name, product_name, size, price, action):
    """Customer ಗೆ booking status WhatsApp ಕಳಿಸು"""
    try:
        if action == "agree":
            msg = (
                f"✅ *Booking Confirmed!*\n\n"
                f"Hi {customer_name}! 🎉\n"
                f"Your order for *{product_name}* (Size: {size}) has been *confirmed*!\n"
                f"Price: *{price}*\n\n"
                f"Our team will contact you soon.\n"
                f"📞 Questions? Call: 9353838835\n\n"
                f"Thank you! 🐬 *Dolphin Trends*"
            )
        elif action == "disagree":
            msg = (
                f"❌ *Out of Stock*\n\n"
                f"Hi {customer_name}, sorry!\n"
                f"*{product_name}* is currently out of stock.\n"
                f"We'll notify you when it's back! 😊\n\n"
                f"📞 Call: 9353838835\n"
                f"🐬 *Dolphin Trends*"
            )
        elif action == "size_unavail":
            msg = (
                f"📏 *Size Not Available*\n\n"
                f"Hi {customer_name}, sorry!\n"
                f"Size *{size}* for *{product_name}* is not available.\n"
                f"Please try a different size or contact us.\n\n"
                f"📞 Call: 9353838835\n"
                f"🐬 *Dolphin Trends*"
            )
        else:
            return

        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        payload = {
            "chatId": f"{customer_phone}@c.us",
            "message": msg
        }
        requests.post(url, json=payload, timeout=30)
        print(f"✅ Customer WhatsApp sent ({action})!")
    except Exception as e:
        print(f"Customer WhatsApp Error: {e}")

# ================= LIFESPAN =================
@asynccontextmanager
async def lifespan(app: FastAPI):
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook", timeout=10)
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": f"{BACKEND_URL}/webhook"},
                timeout=10
            )
            print(f"✅ Telegram webhook set: {r.json()}")
        except Exception as e:
            print(f"Webhook setup error: {e}")
    yield

# ================= APP =================
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ================= ROOT =================
@app.get("/")
def home():
    return {"status": "✅ Dolphin Trends Backend Active!", "version": "2.0"}

@app.head("/")
def home_head():
    return {}

# ================================================================
#  PRODUCTS ROUTES
# ================================================================

@app.get("/products")
def get_products():
    """ಎಲ್ಲಾ products ತರು"""
    if products_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    try:
        products = list(products_col.find({}))
        result = []
        for p in products:
            p["_id"] = str(p["_id"])
            if "product_id" not in p:
                p["product_id"] = p["_id"]
            result.append(p)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products")
async def add_product(
    name: str = Form(...),
    price: str = Form(...),
    original_price: str = Form(""),
    description: str = Form(""),
    category: str = Form("Tops"),
    available: str = Form("true"),
    file: Optional[UploadFile] = File(None)
):
    """ಹೊಸ product add ಮಾಡು"""
    if products_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    image_url = ""
    
    # Image upload to Cloudinary
    if file:
        try:
            contents = await file.read()
            result = cloudinary.uploader.upload(contents, folder="dolphin_trends", resource_type="image")
            image_url = result.get("secure_url", "")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")
    
    product_id = str(uuid.uuid4())
    product_data = {
        "product_id": product_id,
        "name": name,
        "price": price if price.startswith("₹") else f"₹{price}",
        "original_price": original_price if not original_price or original_price.startswith("₹") else f"₹{original_price}",
        "description": description,
        "category": category,
        "image": image_url,
        "available": available.lower() == "true"
    }
    
    products_col.insert_one(product_data)
    product_data["_id"] = str(product_data["_id"])
    return product_data

@app.put("/products/{product_id}")
async def update_product(product_id: str, request: Request):
    """Product update ಮಾಡು (text fields)"""
    if products_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    data = await request.json()
    
    update_fields = {}
    if "name" in data:         update_fields["name"] = data["name"]
    if "price" in data:        update_fields["price"] = data["price"]
    if "original_price" in data: update_fields["original_price"] = data["original_price"]
    if "description" in data:  update_fields["description"] = data["description"]
    if "category" in data:     update_fields["category"] = data["category"]
    if "available" in data:    update_fields["available"] = data["available"]
    
    result = products_col.update_one(
        {"product_id": product_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        # Try with _id
        try:
            result = products_col.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_fields}
            )
        except:
            raise HTTPException(status_code=404, detail="Product not found")
    
    return {"status": "updated", "product_id": product_id}

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    """Product delete ಮಾಡು"""
    if products_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    result = products_col.delete_one({"product_id": product_id})
    
    if result.deleted_count == 0:
        try:
            result = products_col.delete_one({"_id": ObjectId(product_id)})
        except:
            pass
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
    
    return {"status": "deleted"}

# ================================================================
#  BOOKINGS ROUTES
# ================================================================

@app.get("/bookings")
def get_bookings():
    """ಎಲ್ಲಾ bookings ತರು"""
    if bookings_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    try:
        bookings = list(bookings_col.find({}))
        result = []
        for b in bookings:
            b["_id"] = str(b["_id"])
            if "booking_id" not in b:
                b["booking_id"] = b["_id"]
            result.append(b)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bookings")
async def create_booking(request: Request, background_tasks: BackgroundTasks):
    """ಹೊಸ booking create ಮಾಡು"""
    if bookings_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    data = await request.json()
    
    booking_id = str(uuid.uuid4())
    booking = {
        "booking_id": booking_id,
        "customer_name": data.get("customer_name", ""),
        "customer_phone": data.get("customer_phone", ""),
        "product_name": data.get("product_name", ""),
        "image_url": data.get("image_url", ""),
        "size": data.get("size", ""),
        "price": data.get("price", ""),
        "status": "Pending"
    }
    
    bookings_col.insert_one(booking)
    booking["_id"] = str(booking["_id"])
    
    # Admin ಗೆ WhatsApp notification
    if GREEN_API_INSTANCE and GREEN_API_TOKEN:
        admin_msg = (
            f"🛍️ *New Booking Request!*\n\n"
            f"👗 *Product:* {booking['product_name']}\n"
            f"📏 *Size:* {booking['size']}\n"
            f"💰 *Price:* {booking['price']}\n"
            f"👤 *Customer:* {booking['customer_name']}\n"
            f"📱 *Phone:* {booking['customer_phone']}\n\n"
            f"⚙️ Admin Panel: {FRONTEND_URL}"
        )
        background_tasks.add_task(
            send_whatsapp_group_message, admin_msg
        )
    
    return booking

def send_whatsapp_group_message(message):
    try:
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        payload = {"chatId": YOUR_WHATSAPP_GROUP_ID, "message": message}
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Group WhatsApp Error: {e}")

@app.post("/api/admin/update-booking")
async def update_booking_status(
    booking_id: str,
    action: str,
    background_tasks: BackgroundTasks
):
    """Booking status update ಮಾಡು + customer ಗೆ notify ಮಾಡು"""
    if bookings_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    status_map = {
        "agree": "Approved",
        "disagree": "No Stock",
        "size_unavail": "Size Unavailable"
    }
    
    new_status = status_map.get(action)
    if not new_status:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    result = bookings_col.find_one_and_update(
        {"booking_id": booking_id},
        {"$set": {"status": new_status}},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Customer ಗೆ WhatsApp notification
    if GREEN_API_INSTANCE and GREEN_API_TOKEN:
        background_tasks.add_task(
            send_whatsapp_notification,
            result.get("customer_phone", ""),
            result.get("customer_name", ""),
            result.get("product_name", ""),
            result.get("size", ""),
            result.get("price", ""),
            action
        )
    
    return {"status": "updated", "new_status": new_status}

@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: str):
    """Booking delete ಮಾಡು"""
    if bookings_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    result = bookings_col.delete_one({"booking_id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"status": "deleted"}

# ================================================================
#  REVIEWS ROUTES
# ================================================================

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    """Product ಗೆ reviews ತರು"""
    if reviews_col is None:
        return []
    try:
        reviews = list(reviews_col.find({"product_id": product_id}))
        for r in reviews:
            r["_id"] = str(r["_id"])
            if "id" not in r:
                r["id"] = r["_id"]
        return reviews
    except Exception as e:
        return []

@app.post("/reviews")
async def add_review(request: Request):
    """Review add ಮಾಡು"""
    if reviews_col is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    data = await request.json()
    
    review = {
        "id": str(uuid.uuid4()),
        "product_id": data.get("product_id", ""),
        "name": data.get("name", "Anonymous"),
        "text": data.get("text", ""),
        "rating": data.get("rating", 5)
    }
    
    reviews_col.insert_one(review)
    review["_id"] = str(review["_id"])
    return review

# ================================================================
#  TELEGRAM WEBHOOK
# ================================================================

@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Telegram bot webhook — photo upload ಮಾಡಿದಾಗ product add ಮಾಡು"""
    try:
        data = await request.json()
        print(f"📩 Webhook received: {data}")
        
        if "message" not in data:
            return {"status": "ok"}
        
        msg = data["message"]
        chat_id = msg.get("chat", {}).get("id")
        
        # ✅ Photo upload handling
        if "photo" in msg:
            caption = msg.get("caption", "New Product")
            lines = caption.split('\n')
            
            # Caption format:
            # Line 1: Product Name
            # Line 2: Price (e.g. 500)
            # Line 3: Category (e.g. Kurtha Sets)
            # Line 4: Description (optional)
            
            name        = lines[0].strip() if len(lines) > 0 else "New Product"
            price       = lines[1].strip() if len(lines) > 1 else ""
            category    = lines[2].strip() if len(lines) > 2 else "Tops"
            description = lines[3].strip() if len(lines) > 3 else "Curated boutique wear."
            
            # Telegram file download
            file_id = msg["photo"][-1]["file_id"]
            f_info = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
                params={"file_id": file_id},
                timeout=15
            ).json()
            f_path = f_info.get("result", {}).get("file_path")
            
            if not f_path:
                send_telegram_reply(chat_id, "❌ File path get ಆಗ್ಲಿಲ್ಲ! Try again.")
                return {"status": "error"}
            
            img_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{f_path}"
            
            # Upload to Cloudinary
            send_telegram_reply(chat_id, "⏳ Image upload ಆಗ್ತಿದೆ...")
            perm_url = upload_to_cloudinary(img_url)
            
            if not perm_url:
                send_telegram_reply(chat_id, "❌ Cloudinary upload failed! Check API keys.")
                return {"status": "error"}
            
            # Save to MongoDB
            if products_col is not None:
                product_id = str(uuid.uuid4())
                product_data = {
                    "product_id": product_id,
                    "name": name,
                    "price": f"₹{price}" if price and not price.startswith("₹") else price,
                    "original_price": "",
                    "description": description,
                    "category": category,
                    "image": perm_url,
                    "available": True
                }
                products_col.insert_one(product_data)
                
                # WhatsApp notification
                background_tasks.add_task(send_whatsapp, perm_url, name, description, price)
                
                # ✅ Telegram ಗೆ success reply
                send_telegram_reply(
                    chat_id,
                    f"✅ *Product Added Successfully!*\n\n"
                    f"👗 *Name:* {name}\n"
                    f"💰 *Price:* ₹{price}\n"
                    f"🏷️ *Category:* {category}\n"
                    f"🖼️ *Image:* Uploaded ✅\n\n"
                    f"🌐 Website: {FRONTEND_URL}"
                )
            else:
                send_telegram_reply(chat_id, "❌ Database connected ಆಗಿಲ್ಲ! MONGO_URL check ಮಾಡಿ.")
        
        # Text message handling
        elif "text" in msg:
            text = msg.get("text", "").strip()
            if text == "/start":
                send_telegram_reply(
                    chat_id,
                    "🐬 *Dolphin Trends Bot Active!*\n\n"
                    "Photo + Caption ಕಳಿಸಿ product add ಮಾಡಿ:\n\n"
                    "*Format:*\n"
                    "Line 1: Product Name\n"
                    "Line 2: Price (numbers only)\n"
                    "Line 3: Category\n"
                    "Line 4: Description\n\n"
                    "*Example:*\n"
                    "Silk Kurti\n"
                    "850\n"
                    "Kurtha Sets\n"
                    "Beautiful red silk kurti"
                )
            elif text == "/products":
                count = products_col.count_documents({}) if products_col else 0
                send_telegram_reply(chat_id, f"📦 Total products in DB: *{count}*")
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"status": "error", "detail": str(e)}
