from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from tinydb import TinyDB, Query
import os
import uuid
import requests
import shutil
import re
import certifi
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

# ================= UPLOADS =================

os.makedirs("uploads", exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

# ================= ENV =================

MONGO_URL = os.environ.get("MONGO_URL", "")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

HF_TOKEN = os.environ.get("HF_TOKEN", "")

GREEN_API_ID = os.environ.get("GREEN_API_ID", "")

GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")

WHATSAPP_NUMBER = os.environ.get(
    "WHATSAPP_NUMBER",
    "917411255628@c.us"
)

FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

BACKEND_URL = "https://dolphin-trends-3.onrender.com"

# ================= GOOGLE GEMINI =================

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("✅ Gemini Configured")

# ================= DATABASE =================

if MONGO_URL:

    client = MongoClient(
        MONGO_URL,
        tls=True,
        tlsCAFile=certifi.where()
    )

    db = client["dolphin_trends_db"]

    products_table = db["products"]

    mongodb_mode = True

    print("✅ MongoDB Connected")

else:

    local_db = TinyDB("database.json")

    products_table = local_db.table("products")

    mongodb_mode = False

    print("⚠️ TinyDB Mode")

# ================= HELPERS =================

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

def send_whatsapp(image_url, product_name):

    try:

        url = (
            f"https://api.green-api.com/waInstance"
            f"{GREEN_API_ID}/sendFileByUrl/"
            f"{GREEN_API_TOKEN}"
        )

        caption = (
            f"🛍️ Dolphin Trends\n\n"
            f"✨ {product_name}\n\n"
            f"🌐 Shop Now:\n"
            f"{FRONTEND_URL}"
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

    if mongodb_mode:

        products = list(
            products_table.find({}, {"_id": 0})
        )

        return products

    return products_table.all()

# ================= ADD PRODUCT =================

@app.post("/upload-from-bot")
async def upload_from_bot(

    file: UploadFile = File(...),

    category: str = Form("Kurta Sets"),

    name: str = Form("Fashion Product"),

    price: str = Form("499"),

    original_price: str = Form("799"),

    description: str = Form("Premium Fashion")
):

    try:

        # ================= SAVE ORIGINAL =================

        ext = file.filename.split(".")[-1]

        filename = str(uuid.uuid4()) + "." + ext

        filepath = "uploads/" + filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_url = BACKEND_URL + "/uploads/" + filename

        final_image_url = image_url

        # ================= AI IMAGE GENERATION =================

        try:

            hf_url = (
                "https://api-inference.huggingface.co/models/"
                "stabilityai/stable-diffusion-xl-base-1.0"
            )

            headers = {
                "Authorization": f"Bearer {HF_TOKEN}"
            }

            prompt = (
                f"A beautiful stylish Indian female model "
                f"wearing the exact same {category}, "
                f"same cloth design, same color, "
                f"same pattern, full body, "
                f"2 stylish poses side by side, "
                f"white studio background, "
                f"professional fashion photography"
            )

            payload = {
                "inputs": prompt
            }

            ai_response = requests.post(
                hf_url,
                headers=headers,
                json=payload,
                timeout=120
            )

            if ai_response.status_code == 200:

                ai_filename = (
                    str(uuid.uuid4()) + ".jpg"
                )

                ai_filepath = (
                    "uploads/" + ai_filename
                )

                with open(ai_filepath, "wb") as f:
                    f.write(ai_response.content)

                final_image_url = (
                    BACKEND_URL +
                    "/uploads/" +
                    ai_filename
                )

                print("✅ AI IMAGE CREATED")

            else:

                print("HF ERROR:", ai_response.text)

        except Exception as e:

            print("AI IMAGE ERROR:", str(e))

        # ================= CATEGORY PRICE =================

        cat_lower = category.lower().strip()

        auto_price = DEFAULT_PRICES.get(
            cat_lower,
            500
        )

        if price == "499":
            price = str(auto_price)

        original_price = str(
            int(float(price) * 1.4)
        )

        # ================= PRODUCT =================

        product = {
            "id": str(uuid.uuid4()),
            "name": name,
            "price": "Rs." + price,
            "original_price": "Rs." + original_price,
            "description": description,
            "category": category,
            "image": final_image_url,
            "available": True
        }

        # ================= SAVE DB =================

        if mongodb_mode:

            products_table.insert_one(product)

        else:

            products_table.insert(product)

        # ================= WHATSAPP =================

        send_whatsapp(
            final_image_url,
            name
        )

        return {
            "success": True,
            "product": product
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# ================= DELETE =================

@app.delete("/products/{product_id}")
def delete_product(product_id: str):

    try:

        if mongodb_mode:

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

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# ================= ROOT =================

@app.get("/")
def home():

    return {
        "status": "Dolphin Trends Backend Live"
            }
                        
