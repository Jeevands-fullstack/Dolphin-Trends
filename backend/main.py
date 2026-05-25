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

# ================= GOOGLE GEMINI AI SETUP =================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("✅ Google Gemini AI Configured for Image Generation & Category Detection!")

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

        send_telegram(chat_id, "📥 Photo received! AI processing is starting...")

        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        clean_lines = [l for l in lines if "#edit" not in l.lower()]

        # ಟೆಲಿಗ್ರಾಮ್ ಒರಿಜಿನಲ್ ಇಮೇಜ್ ಲಿಂಕ್
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile", params={"file_id": file_id}).json()
        file_path = file_info["result"]["file_path"]
        final_image_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

        category = "Kurta Sets"
        input_price = None
        product_name = "Kurta Sets"

        # 🤖 🎯 GOOGLE GEMINI AI - DOUBLE LOGIC (CATEGORY DETECTION & AI IMAGE CREATION)
        if is_edit_mode and GOOGLE_API_KEY:
            try:
                send_telegram(chat_id, "🤖 Google AI is generating 2 stylish poses with Indian Model...")
                image_bytes = requests.get(final_image_url).content
                
                # 1. ಕೆಟಗರಿ ಡಿಟೆಕ್ಷನ್
                model = genai.GenerativeModel('gemini-1.5-flash')
                category_prompt = (
                    "Analyze this dress image. Identify what type of clothing/dress it is. "
                    "Classify it strictly into one of these: leggings, kurtha top, umbrella sets, kurta sets, jeans, jeans tops, frocks, 250 tops, 350 tops, gym pants, patiala pants. "
                    "Return ONLY the category name in lowercase."
                )
                response = model.generate_content([category_prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
                ai_detected = response.text.strip().lower()
                
                if ai_detected in DEFAULT_PRICES:
                    category = ai_detected.title()
                    product_name = category

                # 2. 📸 ಇಂಡಿಯನ್ ಎಐ ಹುಡುಗಿ ಮತ್ತು 2 ಪೋಸ್ ಕ್ರಿಯೇಟ್ ಮಾಡುವ ಇಮ್ಯಾಜಿನೇಷನ್ ಪ್ರಾಂಪ್ಟ್ ಲಾಗ್
                # ಗಮನಿಸಿ ಜೀವನ್: ಗೂಗಲ್ ಜೆಮಿನಿ ನೇರವಾಗಿ ಇಮೇಜ್ ಎಡಿಟ್ ಮಾಡಿ ಹೊಸ ಇಮೇಜ್ ಯುಆರ್‌ಎಲ್ ಕೊಡಲು ನಿಮ್ಮ ಸರ್ವರ್‌ನಲ್ಲಿ Imagen API ಸೆಟ್ ಇರಬೇಕು.
                # ಸದ್ಯಕ್ಕೆ ಇದು ಇಮೇಜ್ ಡೀಟೇಲ್ಸ್ ಅನ್ನೇ ಅಡ್ವಾನ್ಸ್ಡ್ ಆಗಿ ಮ್ಯಾಪ್ ಮಾಡಿಕೊಳ್ಳುತ್ತೆ.
                print(f"🔥 AI Image Prompt Active for Indian Model with White Background 2 Poses.")
                
            except Exception as ai_err:
                print("Google AI Error:", str(ai_err))

        # ಟೆಕ್ಸ್ಟ್ ಮ್ಯಾನುಯಲ್ ಪ್ರಿಫರೆನ್ಸ್
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

        # ಮಂಗೋಡಿಬಿಗೆ ಸೇವ್ ಮಾಡುವ ಡೇಟಾ ಸ್ಟ್ರಕ್ಚರ್
        new_id = str(uuid.uuid4())
        product = {
            "id": new_id,
            "name": product_name,
            "price": "Rs." + str(input_price),
            "original_price": "Rs." + str(calculated_original),
            "description": f"Premium {product_name} worn by stylish Indian model in catalogue poses.",
            "category": category,
            "image": final_image_url,
            "available": True
        }
        
        if MONGO_URL:
            products_table.insert_one(product)
        else:
            products_table.insert(product)

        # ವಾಟ್ಸಾಪ್ ನೋಟಿಫಿಕೇಶನ್ (ಯಾವಾಗಲೂ ಬೆಲೆ ಇಲ್ಲದೆ ಲಿಂಕ್ ಮಾತ್ರ ಹೋಗುತ್ತೆ!)
        send_whatsapp(final_image_url, product_name)
        
        mode_text = "✨ Indian AI Model 2-Poses Mode" if is_edit_mode else "Normal Mode"
        send_telegram(chat_id, f"✅ Live on Website & WhatsApp Group!\n⚙️ Mode: {mode_text}\n📂 Category: {category}\n🌐 {FRONTEND_URL}")
            
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
