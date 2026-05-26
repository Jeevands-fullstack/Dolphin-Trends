from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import uuid
import requests
import json
import re
import google.generativeai as genai

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
import certifi # 🛡️ ಸೆಕ್ಯೂರಿಟಿ ಸರ್ಟಿಫಿಕೇಟ್ ಮ್ಯಾಚ್ ಮಾಡಲು ಇದನ್ನು ಇಂಪೋರ್ಟ್ ಮಾಡಬೇಕು

ca = certifi.where() # ಪಕ್ಕಾ ಸರ್ಟಿಫಿಕೇಟ್ ಪಾತ್ ತಗೊಳ್ಳುತ್ತೆ

MONGO_URL = os.environ.get("MONGO_URL", "")
if MONGO_URL:
    # 🔥 ಇಲ್ಲಿ tlsCAFile=ca ಆಡ್ ಮಾಡಿದ್ದೀವಿ, ಇದು SSL ಎರರ್ ಅನ್ನು 100% ಸಾಲ್ವ್ ಮಾಡುತ್ತೆ!
    client = MongoClient(
        MONGO_URL, 
        tlsCAFile=ca
    )
    db = client["dolphin_trends_db"]
    products_table = db["products"]
    print("✅ Connected to MongoDB Atlas Successfully!")
else:
    from tinydb import TinyDB
    local_db = TinyDB("database.json")
    products_table = local_db.table("products")
# ================= GOOGLE GEMINI AI SETUP =================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("✅ Google Gemini AI Configured for Category Detection!")

# ================= ENV VARIABLES =================
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

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

# 🔔 ವಾಟ್ಸಾಪ್ ಫಂಕ್ಷನ್ - ಪ್ರೈಸ್ ಇಲ್ಲದೆ ಲಿಂಕ್ ಮಾತ್ರ ಹೋಗುತ್ತೆ
def send_whatsapp(image_url, display_name):
    try:
        clean_name = re.sub(r'\d+', '', display_name).replace('Rs.', '').strip()
        clean_name = " ".join(clean_name.split()).title()

        caption = (
            f"🔥 *New Arrival: Premium {clean_name}*\n"
            f"💃 *Check out this beautiful trend! Grab yours before it's gone.*\n\n"
            f"👇 *Click here to see full details & Shop Now:*\n{FRONTEND_URL}"
        )

        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByUrl/{GREEN_API_TOKEN}"
        payload = {"chatId": WHATSAPP_NUMBER, "urlFile": image_url, "fileName": "product.jpg", "caption": caption}
        requests.post(url, json=payload, timeout=60)
        return True
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# 📸 INSTAGRAM AUTOMATIC UPLOAD (FUTURE USE - ಸದ್ಯಕ್ಕೆ ಇನ್-ಆಕ್ಟಿವ್ ಆಗಿದೆ)
def upload_to_instagram(image_url, caption_text):
    if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        return False
    try:
        url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
        payload = {"image_url": image_url, "caption": caption_text, "access_token": INSTAGRAM_ACCESS_TOKEN}
        response = requests.post(url, data=payload).json()
        creation_id = response.get("id")

        if creation_id:
            publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
            publish_payload = {"creation_id": creation_id, "access_token": INSTAGRAM_ACCESS_TOKEN}
            requests.post(publish_url, data=publish_payload)
            return True
        return False
    except Exception as e:
        print("Instagram Error:", str(e))
        return False

# ================= TELEGRAM WEBHOOK =================
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        
        if not chat_id or "photo" not in message:
            return {"ok": True}

        caption = message.get("caption", "").strip()
        is_edit_mode = "#edit" in caption.lower()

        send_telegram(chat_id, "📥 Photo received, starting processing...")

        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        clean_lines = [l for l in lines if "#edit" not in l.lower()]

        # ಟೆಲಿಗ್ರಾಮ್ ಇಮೇಜ್ ಲಿಂಕ್ ತಗೊಳೋದು
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile", params={"file_id": file_id}).json()
        file_path = file_info.get("result", {}).get("file_path")
        
        if not file_path:
            send_telegram(chat_id, "❌ Telegram image download failed!")
            return {"ok": True}
            
        final_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

        category = "Kurta Sets"
        input_price = None
        product_name = "Kurta Sets"

        # 🤖 🎯 GOOGLE GEMINI AI - WITH SAFE FALLBACK
        if is_edit_mode:
            if GOOGLE_API_KEY:
                try:
                    send_telegram(chat_id, "🤖 Google AI is scanning the dress category...")
                    image_bytes = requests.get(final_image_url).content
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    category_prompt = (
                        "Identify the exact clothing type from this image. "
                        "Classify strictly into: leggings, kurtha top, umbrella sets, kurta sets, jeans, jeans tops, frocks, 250 tops, 350 tops, gym pants, patiala pants. "
                        "Return ONLY the category name in lowercase."
                    )
                    response = model.generate_content([category_prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
                    ai_detected = response.text.strip().lower()
                    
                    if ai_detected in DEFAULT_PRICES:
                        category = ai_detected.title()
                        product_name = category
                except Exception as ai_err:
                    print("Google AI Error:", str(ai_err))
                    send_telegram(chat_id, "⚠️ AI Scan failed, using default category.")
            else:
                send_telegram(chat_id, "⚠️ GOOGLE_API_KEY missing in Render! Using default category.")

        # ಮ್ಯಾನುಯಲ್ ಟೆಕ್ಸ್ಟ್ ಪ್ರಿಫರೆನ್ಸ್ ಚೆಕ್
        if clean_lines:
            if 'price' not in clean_lines[0].lower():
                category = clean_lines[0].strip()
                
            for line in clean_lines:
                if 'price' in line.lower():
                    match = re.search(r'price\s*:\s*(\d+)', line.lower())
                    if match: input_price = int(match.group(1))
            
            name_parts = [line for line in clean_lines if 'price' not in line.lower() and line.strip() != category]
            if name_parts:
                product_name = " ".join(name_parts)
            else:
                product_name = category

        if input_price is None:
            input_price = DEFAULT_PRICES.get(category.lower().strip(), 1200)

        calculated_original = int(input_price * 1.40)

        # ಮಂಗೋಡಿಬಿಗೆ ಸೇವ್ ಮಾಡೋದು
        new_id = str(uuid.uuid4())
        product = {
            "id": new_id,
            "name": product_name,
            "price": "Rs." + str(input_price),
            "original_price": "Rs." + str(calculated_original),
            "description": f"Premium {product_name} from Dolphin Trends Catalog.",
            "category": category,
            "image": final_image_url,
            "available": True
        }
        
        try:
            if MONGO_URL:
                products_table.insert_one(product)
            else:
                products_table.insert(product)
        except Exception as db_err:
            print("Database Error:", str(db_err))
            send_telegram(chat_id, "❌ MongoDB Save Failed! Check your MONGO_URL.")
            return {"ok": True}

        # ವಾಟ್ಸಾಪ್ ಗ್ರೂಪ್‌ಗೆ ಸೆಂಡ್
        send_whatsapp(final_image_url, product_name)
        
        # ಇನ್‌ಸ್ಟಾಗ್ರಾಮ್ ಪ್ರಿಪ್ರೇಷನ್
        insta_caption = f"🔥 New Arrival: {product_name}\n💃 Check it out on our website!\n🌐 {FRONTEND_URL}"
        upload_to_instagram(final_image_url, insta_caption)
        
        mode_text = "🤖 Google AI Scanner" if is_edit_mode else "Normal"
        send_telegram(chat_id, f"✅ Live on Website & Sent to WhatsApp!\n⚙️ Mode: {mode_text}\n📂 Category: {category}\n🌐 {FRONTEND_URL}")
            
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
