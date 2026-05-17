from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tinydb import TinyDB, Query
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import uuid
import requests
import google.generativeai as genai  # ಗೂಗಲ್ ಜೆಮಿನಿ ಲೈಬ್ರರಿ

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = TinyDB('database.json')
products_table = db.table('products')
bookings_table = db.table('bookings')
reviews_table = db.table('reviews')

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ⚠️ ನಿಮ್ಮ ನಿಜವಾದ ಟೋಕನ್‌ಗಳನ್ನು ಇಲ್ಲಿ ಹಾಕಿ
HF_TOKEN = "your_token_here"
GEMINI_API_KEY = "your_gemini_api_key_here"  # ನಿಮ್ಮ Gemini API ಕೀ ಇಲ್ಲಿ ಹಾಕಿ

# ಜೆಮಿನಿ ಕಾನ್ಫಿಗರೇಶನ್
genai.configure(api_key=GEMINI_API_KEY)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[str] = None
    original_price: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    available: Optional[bool] = None

@app.get("/products")
def get_products():
    return products_table.all()

# ─────────────────────────────────────────
# ✅ POST - Add product (From Admin Panel)
# ─────────────────────────────────────────
@app.post("/products")
async def add_product(
    name: str = Form(...),
    price: str = Form(...),
    original_price: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...)
):
    ext = file.filename.split(".")[-1]
    filename = str(uuid.uuid4()) + "." + ext
    filepath = "uploads/" + filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    product = {
        "id": str(uuid.uuid4()),
        "name": name,
        "price": price,
        "original_price": original_price,
        "description": description,
        "category": category,
        "image": "https://dolphin-trends.onrender.com/uploads/" + filename,
        "available": True
    }
    products_table.insert(product)
    return product

# ─────────────────────────────────────────
# 🤖 ಹೊಸ ಎಂಡ್ ಪಾಯಿಂಟ್: ಟೆಲಿಗ್ರಾಂ ಬೋಟ್ ಮತ್ತು ಜೆಮಿನಿ ಆಟೋಮೇಷನ್‌ಗಾಗಿ
# ─────────────────────────────────────────
@app.post("/upload-from-bot")
async def upload_from_bot(file: UploadFile = File(...), category: str = Form("All")):
    try:
        # 1. ಫೋಟೋವನ್ನು ಮೊದಲು ಸರ್ವರ್‌ನಲ್ಲಿ ಸೇವ್ ಮಾಡಿ
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = str(uuid.uuid4()) + "." + ext
        filepath = f"uploads/{filename}"

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. ಜೆಮಿನಿ ಅಪ್‌ಡೇಟೆಡ್ ಮಾಡೆಲ್ (gemini-2.5-flash) ಕಾಲ್ ಮಾಡಿ ಡಿಸ್ಕ್ರಿಪ್ಷನ್ ರೆಡಿ ಮಾಡುವುದು
        # ಉಚಿತ ಟೈರ್‌ನಲ್ಲಿ 100% ವರ್ಕ್ ಆಗುತ್ತದೆ
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # ಇಮೇಜ್ ರೀಡ್ ಮಾಡುವುದು
        with open(filepath, "rb") as f:
            image_bytes = f.read()
            
        image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]
        
        prompt = (
            "You are an expert fashion catalog writer for Dolphin Trends, Bangalore. "
            "Look at this women's clothing item and generate: "
            "1. A catchy product name. "
            "2. An attractive product description in Kannada and English mixed. "
            "Give the output clearly."
        )

        response = model.generate_content([prompt, image_parts[0]])
        generated_text = response.text if response.text else "Beautiful Women's Fashion Wear"

        # 3. ಪ್ರಾಡಕ್ಟ್ ಅನ್ನು ಡೇಟಾಬೇಸ್‌ಗೆ ಸೇರಿಸುವುದು
        product = {
            "id": str(uuid.uuid4()),
            "name": f"Dolphin Trendy {category}",
            "price": "₹499",  # ಬೆಲೆಯನ್ನು ನೀವು ಆಮೇಲೆ ಎಡಿಟ್ ಮಾಡಬಹುದು
            "original_price": "₹899",
            "description": generated_text,
            "category": category,
            "image": "https://dolphin-trends.onrender.com/uploads/" + filename,
            "available": True
        }
        products_table.insert(product)

        return {"success": True, "product": product}

    except Exception as e:
        return {"success": False, "error": str(e)}

# ─────────────────────────────────────────
# ✅ PUT - Edit product
# ─────────────────────────────────────────
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

# ─────────────────────────────────────────
# ✅ DELETE - Delete product
# ─────────────────────────────────────────
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

@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    Review = Query()
    return reviews_table.search(Review.product_id == product_id)

@app.post("/reviews")
def add_review(review: dict):
    review["id"] = str(uuid.uuid4())
    reviews_table.insert(review)
    return review

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

@app.post("/generate-model-image")
async def generate_model_image(file: UploadFile = File(...)):
    try:
        API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-3.5-large/text-to-image"
        headers = {"Authorization": "Bearer " + HF_TOKEN}
        payload = {
            "inputs": "A beautiful young Indian woman wearing an elegant traditional dress, fashion photography, studio white background, full body shot, professional model photo"
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            gen_filename = str(uuid.uuid4()) + ".png"
            gen_filepath = "uploads/" + gen_filename
            with open(gen_filepath, "wb") as f:
                f.write(response.content)
            return {"success": True, "image_url": "https://dolphin-trends.onrender.com/uploads/" + gen_filename}
        else:
            return {"success": False, "error": "HF API error " + str(response.status_code)}
    except Exception as e:
        return {"success": False, "error": str(e)}