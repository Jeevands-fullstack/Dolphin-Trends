from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import uuid
import requests
import json
import re

# ================= FASTAPI SETUP =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MONGODB ATLAS SETUP =================
MONGO_URL = os.environ.get("MONGO_URL", "")

if MONGO_URL:
    client = MongoClient(MONGO_URL)
    db = client["dolphin_trends_db"]
    products_table = db["products"]
    print("✅ Connected to MongoDB Atlas Successfully!")
else:
    from tinydb import TinyDB
    local_db = TinyDB("database.json")
    products_table = local_db.table("products")
    print("⚠️ Using local TinyDB Backup.")

# ================= ENV VARIABLES =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GREEN_API_ID = os.environ.get("GREEN_API_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "917411255628@c.us")
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

DEFAULT_PRICES = {
    "leggings": 200, "kurtha top": 200, "umbrella sets": 1000,
    "kurta sets": 1200, "jeans": 550, "jeans tops": 300,
    "frocks": 850, "250 tops": 250, "350 tops": 350,
    "gym pants": 300, "patiala pants": 200
}

# ================= HELPERS =================
def send_telegram(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": text})

def send_whatsapp(image_url, display_name):
    try:
        clean_name = re.sub(r'\d+', '', display_name).replace('Rs.', '').strip()
        clean_name = " ".join(clean_name.split()).title()

        caption = (
            f"🔥 *Hurry! Limited Stock!*\n\n"
            f"✨ *New Arrival: Premium {clean_name}*\n"
            f"💃 *Grab yours before it's gone!*\n\n"
            f"👇 *Check Price & Shop Now:*\n{FRONTEND_URL}"
        )
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {"chatId": WHATSAPP_NUMBER, "urlFile": image_url, "fileName": "product.jpg", "caption": caption}
        requests.post(url, json=payload, timeout=60)
        return True
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= HEALTH CHECK =================
@app.get("/")
def home():
    status = "Active" if MONGO_URL else "Running on Backup"
    return {"status": f"Dolphin Trends API - MongoDB Cloud is {status}"}

# ================= TELEGRAM WEBHOOK (EDIT & NEW UPLOAD) =================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return {"ok": True}

        caption = message.get("caption", "").strip()
        is_edit = "#edit" in caption.lower()

        # ಫೋಟೋ ಇಲ್ಲದೆ ಬರೀ ಟೆಕ್ಸ್ಟ್ ಕಳಿಸಿದ್ರೂ ಎಡಿಟ್ ಆಗೋಕೆ ಹೆಲ್ಪ್ ಮಾಡುತ್ತೆ
        if "photo" not in message and not is_edit:
            return {"ok": True}

        send_telegram(chat_id, "📥 Processing your request...")

        # ಮೆಸೇಜ್ ಲೈನ್‌ಗಳನ್ನು ಕ್ಲೀನ್ ಮಾಡಿಕೊಳ್ಳುವುದು
        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        clean_lines = [l for l in lines if "#edit" not in l.lower()]

        # 🔍 ಕ್ಯಾಪ್ಷನ್‌ನಿಂದ ಪ್ರಾಡಕ್ಟ್ ಐಡಿ ಹುಡುಕೋದು
        target_product_id = None
        for line in clean_lines:
            if "id" in line.lower():
                match = re.search(r'(?:id|product id)\s*:\s*([\w-]+)', line.lower())
                if match:
                    target_product_id = match.group(1).strip()

        # ಐಡಿ ಸಿಕ್ಕಿದ್ರೆ ಆ ಲೈನ್ ಅನ್ನು ಲಿಸ್ಟ್‌ನಿಂದ ಹಟಾಯಿಸುವುದು
        clean_lines = [l for l in clean_lines if "id" not in l.lower()]

        # ಡಿಫಾಲ್ಟ್ ವ್ಯಾಲ್ಯೂಸ್ (ಬರೀ ಫೋಟೋ ಕಳಿಸಿದ್ರೆ ಇವು ಅಪ್ಲೈ ಆಗುತ್ತೆ)
        category = "Kurta Sets"
        input_price = None
        product_name = "Kurta Sets"

        if clean_lines:
            category = clean_lines[0].strip()
            
            for line in clean_lines:
                if 'price' in line.lower():
                    match = re.search(r'price\s*:\s*(\d+)', line.lower())
                    if match: input_price = int(match.group(1))

            name_parts = [line for line in clean_lines[1:] if 'price' not in line.lower()]
            product_name = " ".join(name_parts) if name_parts else category

        if input_price is None:
            input_price = DEFAULT_PRICES.get(category.lower().strip(), 1200)

        calculated_original = int(input_price * 1.40)

        # ಇಮೇಜ್ ಲಿಂಕ್ ತಗೊಳೋದು
        final_image_url = None
        if "photo" in message:
            file_id = message["photo"][-1]["file_id"]
            file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile", params={"file_id": file_id}).json()
            file_path = file_info["result"]["file_path"]
            final_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

        # 🎯 1. ಎಡಿಟಿಂಗ್ ಲಾಜಿಕ್ (#edit ಇದ್ದಾಗ)
        if is_edit:
            if not target_product_id:
                send_telegram(chat_id, "❌ ಎಡಿಟ್ ಮಾಡಲು ಪ್ರಾಡಕ್ಟ್ ಐಡಿ ಕಡ್ಡಾಯ! (Example -> ID: ನಿಮ್ಮ-ಐಡಿ)")
                return {"ok": True}

            if MONGO_URL:
                existing_product = products_table.find_one({"id": target_product_id})
            else:
                from tinydb import Query
                Product = Query()
                res = products_table.search(Product.id == target_product_id)
                existing_product = res[0] if res else None

            if existing_product:
                # ಹೊಸ ಫೋಟೋ ಹಾಕದಿದ್ದರೆ ಹಳೇ ಫೋಟೋನೇ ಇರಲಿ
                img_url = final_image_url if final_image_url else existing_product.get("image")
                
                updated_data = {
                    "name": product_name,
                    "price": "Rs." + str(input_price),
                    "original_price": "Rs." + str(calculated_original),
                    "description": f"Premium {product_name} from Dolphin Trends",
                    "category": category,
                    "image": img_url,
                    "available": True
                }

                if MONGO_URL:
                    products_table.update_one({"id": target_product_id}, {"$set": updated_data})
                else:
                    from tinydb import Query
                    Product = Query()
                    products_table.update(updated_data, Product.id == target_product_id)

                # 🔥 ಎಡಿಟ್ ಆದಾಗ ಬರೀ ಟೆಲಿಗ್ರಾಮ್ ಅಲರ್ಟ್ ಬರುತ್ತೆ, ವಾಟ್ಸಾಪ್‌ಗೆ ಹೋಗಲ್ಲ!
                send_telegram(chat_id, f"✅ Product ID: {target_product_id} Edited in MongoDB Successfully!\n📂 Category: {category}\n🌐 {FRONTEND_URL}")
                return {"ok": True}
            else:
                send_telegram(chat_id, "❌ ಮಂಗೋಡಿಬಿಯಲ್ಲಿ ಈ ಐಡಿಯ ಪ್ರಾಡಕ್ಟ್ ಸಿಗುತ್ತಿಲ್ಲ!")
                return {"ok": True}

        # 🎯 2. ಹೊಸ ಪ್ರಾಡಕ್ಟ್ ಅಪ್‌ಲೋಡ್ ಲಾಜಿಕ್
        else:
            if not final_image_url:
                send_telegram(chat_id, "❌ ಹೊಸ ಪ್ರಾಡಕ್ಟ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಲು ಫೋಟೋ ಕಡ್ಡಾಯ!")
                return {"ok": True}

            new_id = str(uuid.uuid4())
            product = {
                "id": new_id,
                "name": product_name,
                "price": "Rs." + str(input_price),
                "original_price": "Rs." + str(calculated_original),
                "description": f"Premium {product_name} from Dolphin Trends",
                "category": category,
                "image": final_image_url,
                "available": True
            }
            
            if MONGO_URL:
                products_table.insert_one(product)
            else:
                products_table.insert(product)

            # ಹೊಸದಕ್ಕೆ ಮಾತ್ರ ವಾಟ್ಸಾಪ್ ಹೋಗುತ್ತೆ
            send_whatsapp(final_image_url, product_name)
            send_telegram(chat_id, f"✅ Live on MongoDB Cloud!\n📂 Category: {category}\n🆔 ID: {new_id}\n🌐 {FRONTEND_URL}")
            return {"ok": True}
        
    except Exception as e:
        print("Webhook Error:", str(e))
        return {"ok": True}

# ================= PRODUCTS ENDPOINTS =================
@app.get("/products")
def get_products():
    if MONGO_URL:
        return list(products_table.find({}, {"_id": 0}))
    return products_table.all()

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    if MONGO_URL:
        products_table.delete_one({"id": product_id})
    else:
        from tinydb import Query
        Product = Query()
        products_table.remove(Product.id == product_id)
    return {"success": True}
