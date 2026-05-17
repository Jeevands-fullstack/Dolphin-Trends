from fastapi import FastAPI, UploadFile, File, Form # Form ಅನ್ನು ಆಡ್ ಮಾಡಲಾಗಿದೆ
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tinydb import TinyDB, Query
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import uuid
import requests

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

HF_TOKEN = HF_TOKEN = "your_token_here"

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
# ✅ ಸರಿಪಡಿಸಲಾದ POST - Add product
# ─────────────────────────────────────────
@app.post("/products")
async def add_product(
    name: str = Form(...),          # Form(...) ಆಡ್ ಮಾಡಲಾಗಿದೆ
    price: str = Form(...),         # Form(...) ಆಡ್ ಮಾಡಲಾಗಿದೆ
    original_price: str = Form(...),# Form(...) ಆಡ್ ಮಾಡಲಾಗಿದೆ
    description: str = Form(...),   # Form(...) ಆಡ್ ಮಾಡಲಾಗಿದೆ
    category: str = Form(...),      # Form(...) ಆಡ್ ಮಾಡಲಾಗಿದೆ
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