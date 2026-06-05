import os
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import certifi
import cloudinary
import cloudinary.uploader

# Import Instagram automation function from bot.py
from bot import send_instagram_direct

# ================= CONFIGURATION =================
MONGO_URL = os.getenv("MONGO_URL")
GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "https://dolphin-trends-3.onrender.com"

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
products_table = None

if MONGO_URL:
    client = MongoClient(
        MONGO_URL,
        tlsCAFile=ca,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000
    )
    db = client["dolphin_trends_db"]
    products_table = db["products"]


# ================= LIFESPAN =================
@asynccontextmanager
async def lifespan(app: FastAPI):
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
            )
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": f"{BACKEND_URL}/webhook"}
            )
            print("✅ Telegram webhook set successfully")
        except Exception as e:
            print("Webhook setup error:", e)
    yield


# ================= APP =================
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ================= HELPERS =================
def upload_to_cloudinary(image_source):
    try:
        result = cloudinary.uploader.upload(
            image_source,
            folder="dolphin_trends",
            resource_type="image"
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Error: {e}")
        return None


# ================= ROUTES =================
@app.get("/")
def home():
    return {"status": "Dolphin Trends Backend Active!"}


@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()

        if "message" in data and "photo" in data["message"]:
            msg = data["message"]
            caption = msg.get("caption", "")
            file_id = msg["photo"][-1]["file_id"]

            # Get file path from Telegram
            f_info = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
                params={"file_id": file_id}
            ).json()
            f_path = f_info.get("result", {}).get("file_path")

            if not f_path:
                print("❌ Could not get file path from Telegram")
                return {"status": "error", "reason": "file_path missing"}

            img_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{f_path}"

            # Upload to Cloudinary for a permanent URL
            perm_url = upload_to_cloudinary(img_url)

            if perm_url and products_table is not None:
                # Extract name from caption if available
                product_name = "New Product"
                if caption:
                    first_line = caption.split('\n')[0].strip()
                    if first_line:
                        product_name = first_line

                products_table.insert_one({
                    "name": product_name,
                    "image": perm_url,
                    "available": True
                })
                print(f"✅ Product saved to DB: {product_name}")

                # Post to Instagram in background (non-blocking)
                background_tasks.add_task(
                    send_instagram_direct,
                    perm_url,
                    product_name,
                    "Sets"
                )
            else:
                print("⚠️ Cloudinary upload failed or DB not connected")

        return {"status": "ok"}

    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "reason": str(e)}


@app.get("/products")
def get_products():
    if products_table is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        products = list(products_table.find({"available": True}, {"_id": 0}))
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/products")
async def add_product(request: Request):
    try:
        form = await request.form()
        name = form.get("name", "New Product")
        price = form.get("price", "Rs.499")
        original_price = form.get("original_price", "Rs.799")
        description = form.get("description", "")
        category = form.get("category", "Sets")
        file = form.get("file")

        image_url = None
        if file:
            image_bytes = await file.read()
            image_url = upload_to_cloudinary(image_bytes)

        if products_table is not None:
            products_table.insert_one({
                "name": name,
                "price": price,
                "original_price": original_price,
                "description": description,
                "category": category,
                "image": image_url,
                "available": True
            })

        return {"status": "success", "name": name, "image": image_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
