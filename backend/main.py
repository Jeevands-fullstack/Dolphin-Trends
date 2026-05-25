from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from tinydb import TinyDB, Query
import os
import uuid
import requests
import re

# ================= FASTAPI =================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= STATIC FILES =================

os.makedirs("uploads", exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

# ================= MONGODB =================

MONGO_URL = os.environ.get("MONGO_URL", "")

if MONGO_URL:
    client = MongoClient(MONGO_URL)
    db = client["dolphin_trends_db"]
    products_table = db["products"]
    print("✅ MongoDB Connected")
else:
    local_db = TinyDB("database.json")
    products_table = local_db.table("products")
    print("⚠️ TinyDB Local Mode")

# ================= ENV =================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
GREEN_API_ID = os.environ.get("GREEN_API_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get(
    "WHATSAPP_NUMBER",
    "917411255628@c.us"
)

FRONTEND_URL = "https://dolphin-trends-two.vercel.app"
BACKEND_URL = "https://dolphin-trends-3.onrender.com"

# ================= DEFAULT PRICES =================

DEFAULT_PRICES = {
    "leggings": 200,
    "kurtha top": 250,
    "umbrella sets": 1000,
    "kurta sets": 1200,
    "jeans": 550,
    "jeans tops": 350,
    "frocks": 850,
    "250 tops": 250,
    "350 tops": 350,
    "gym pants": 300,
    "patiala pants": 250
}

# ================= TELEGRAM MESSAGE =================

def send_telegram(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=30
        )
    except Exception as e:
        print("Telegram Error:", str(e))

# ================= WHATSAPP =================

def send_whatsapp(image_url, product_name):

    try:

        caption = (
            f"🛍️ *Dolphin Trends*\n\n"
            f"✨ *{product_name}*\n\n"
            f"🔥 New Arrival Available Now\n\n"
            f"🌐 Shop Now:\n{FRONTEND_URL}"
        )

        url = (
            f"https://api.green-api.com/waInstance"
            f"{GREEN_API_ID}/sendFileByUrl/"
            f"{GREEN_API_TOKEN}"
        )

        payload = {
            "chatId": WHATSAPP_NUMBER,
            "urlFile": image_url,
            "fileName": "product.jpg",
            "caption": caption
        }

        response = requests.post(
            url,
            json=payload,
            timeout=60
        )

        print("WhatsApp:", response.text)

    except Exception as e:
        print("WhatsApp Error:", str(e))

# ================= PRODUCTS =================

@app.get("/products")
def get_products():

    if MONGO_URL:
        return list(
            products_table.find({}, {"_id": 0})
        )

    return products_table.all()

# ================= DELETE PRODUCT =================

@app.delete("/products/{product_id}")
def delete_product(product_id: str):

    if MONGO_URL:

        products_table.delete_one({
            "id": product_id
        })

    else:

        Product = Query()

        products_table.remove(
            Product.id == product_id
        )

    return {
        "success": True
    }

# ================= TELEGRAM WEBHOOK =================

@app.post("/webhook")
async def telegram_webhook(request: Request):

    try:

        update = await request.json()

        message = update.get("message", {})

        if "photo" not in message:
            return {"ok": True}

        chat_id = message["chat"]["id"]

        caption = message.get("caption", "")

        is_edit_mode = "#edit" in caption.lower()

        send_telegram(
            chat_id,
            "📥 Photo received..."
        )

        # ================= TELEGRAM IMAGE =================

        file_id = message["photo"][-1]["file_id"]

        file_info = requests.get(
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_TOKEN}/getFile",
            params={
                "file_id": file_id
            }
        ).json()

        file_path = file_info["result"]["file_path"]

        telegram_image_url = (
            f"https://api.telegram.org/file/bot"
            f"{TELEGRAM_TOKEN}/{file_path}"
        )

        image_bytes = requests.get(
            telegram_image_url
        ).content

        # ================= CATEGORY =================

        category = "Kurta Sets"

        lower_caption = caption.lower()

        for cat in DEFAULT_PRICES.keys():

            if cat in lower_caption:
                category = cat.title()

        # ================= PRICE =================

        price = DEFAULT_PRICES.get(
            category.lower(),
            999
        )

        # ================= PRODUCT NAME =================

        clean_caption = (
            caption
            .replace("#edit", "")
            .strip()
        )

        if clean_caption == "":
            clean_caption = category

        product_name = clean_caption

        # ================= AI IMAGE =================

        final_image_url = telegram_image_url

        if is_edit_mode:

            try:

                send_telegram(
                    chat_id,
                    "🎨 Creating AI fashion model..."
                )

                headers = {
                    "Authorization": f"Bearer {HF_TOKEN}",
                    "Content-Type": "application/octet-stream"
                }

                response = requests.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                    headers=headers,
                    data=image_bytes,
                    timeout=120
                )

                if response.status_code == 200:

                    ai_filename = (
                        str(uuid.uuid4()) + ".jpg"
                    )

                    ai_filepath = (
                        "uploads/" + ai_filename
                    )

                    with open(ai_filepath, "wb") as f:
                        f.write(response.content)

                    final_image_url = (
                        f"{BACKEND_URL}/uploads/"
                        f"{ai_filename}"
                    )

                    send_telegram(
                        chat_id,
                        "✅ AI model generated!"
                    )

                else:

                    print(response.text)

                    send_telegram(
                        chat_id,
                        "⚠️ AI failed. Using original image."
                    )

            except Exception as e:

                print("AI ERROR:", str(e))

                send_telegram(
                    chat_id,
                    "⚠️ AI Error. Using original image."
                )

        else:

            # NORMAL MODE SAVE ORIGINAL IMAGE

            original_filename = (
                str(uuid.uuid4()) + ".jpg"
            )

            original_filepath = (
                "uploads/" + original_filename
            )

            with open(original_filepath, "wb") as f:
                f.write(image_bytes)

            final_image_url = (
                f"{BACKEND_URL}/uploads/"
                f"{original_filename}"
            )

        # ================= PRODUCT =================

        product = {
            "id": str(uuid.uuid4()),
            "name": product_name,
            "price": f"Rs.{price}",
            "original_price": f"Rs.{int(price * 1.5)}",
            "description": (
                f"Premium {category} "
                f"Collection from Dolphin Trends"
            ),
            "category": category,
            "image": final_image_url,
            "available": True
        }

        # ================= SAVE DATABASE =================

        if MONGO_URL:

            products_table.insert_one(product)

        else:

            products_table.insert(product)

        # ================= WHATSAPP =================

        send_whatsapp(
            final_image_url,
            product_name
        )

        # ================= SUCCESS =================

        send_telegram(
            chat_id,
            f"✅ Product Live Successfully!\n\n"
            f"🛍️ {product_name}\n"
            f"📂 {category}\n"
            f"💰 Rs.{price}\n\n"
            f"🌐 {FRONTEND_URL}"
        )

        return {
            "ok": True
        }

    except Exception as e:

        print("WEBHOOK ERROR:", str(e))

        return {
            "ok": True
        }

# ================= ROOT =================

@app.get("/")
def home():
    return {
        "message": "Dolphin Trends Backend Running"
        }
