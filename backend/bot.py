import telebot
import requests
from google import genai
from google.genai import types
from PIL import Image
import io
import json

TELEGRAM_TOKEN = "8008263693:AAF9aYopkRzzjPf6VxYZ-oVtOr66UzffYUs"
GEMINI_API_KEY = "AIzaSyDt71UHXS09aeooRBCAEXHRN3ES7I5f1dA"
BACKEND_URL = "https://dolphin-trends.onrender.com"

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        caption = message.caption or ""
        price = ""
        original_price = ""

        for line in caption.split('\n'):
            if 'Price:' in line.strip() or 'price:' in line.strip():
                price = line.split(':')[1].strip()
            if 'Original:' in line.strip() or 'original:' in line.strip():
                original_price = line.split(':')[1].strip()

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = "https://api.telegram.org/file/bot" + TELEGRAM_TOKEN + "/" + file_info.file_path
        photo_response = requests.get(file_url)
        image_bytes = photo_response.content

        bot.reply_to(message, "AI analyzing photo...")

        image = Image.open(io.BytesIO(image_bytes))

        prompt = """This is a women's clothing photo. Please analyze it and provide:
1. Product Name (short, attractive name)
2. Category (choose ONE from: Tops, Leggings, Kurtas, Jeans, Patiala Pants, Sets, Umbrella Tops, Frocks, Western Wear, Gym Pants)
3. Description (2-3 sentences about the clothing)

Respond in this exact JSON format only, no other text:
{
  "name": "product name here",
  "category": "category here",
  "description": "description here"
}"""

        response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[prompt, image]
)

        response_text = response.text.strip()

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        ai_data = json.loads(response_text)
        name = ai_data.get("name", "Fashion Item")
        category = ai_data.get("category", "Tops")
        description = ai_data.get("description", "Beautiful fashion item")

        if not price:
            price = "499"
        if not original_price:
            original_price = str(int(price) + 200)

        bot.reply_to(message, "AI Details:\n" + name + "\n" + category + "\n" + description + "\n\nUploading to website...")

        files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
        data = {
            'name': name,
            'price': price,
            'original_price': original_price,
            'description': description,
            'category': category
        }

        upload_response = requests.post(
            BACKEND_URL + "/products",
            files=files,
            data=data
        )

        if upload_response.status_code == 200:
            bot.reply_to(message, "Successfully uploaded!\n\n" + name + "\nPrice: " + price + "\nCategory: " + category + "\n\nWebsite: https://dolphin-trends-two.vercel.app")
        else:
            bot.reply_to(message, "Upload failed! " + upload_response.text)

    except Exception as e:
        bot.reply_to(message, "Error: " + str(e))

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Welcome to Dolphin Trends Bot!\n\nUpload a photo with caption:\nPrice: 599\nOriginal: 999\n\nAI will automatically generate name, category and description!")

print("Dolphin Trends Bot starting...")
bot.polling(none_stop=True)