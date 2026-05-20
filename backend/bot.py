import os
import io
import json
import re
import requests
import threading
import time
from flask import Flask
from PIL import Image
import telebot

TELEGRAM_TOKEN = "8008263693:AAF9aYopkRzzjPf6VxYZ-oVtOr66UzffYUs"
WEBSITE_URL = "https://dolphin-trends.onrender.com/products"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

GREEN_API_ID = "7107622422"
GREEN_API_TOKEN = "615700ddddfc47b89c6a222ac5464dd45faec9e485a144d885"
WHATSAPP_NUMBER = "917411255628@c.us"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Dolphin Bot is Live!", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    while True:
        try:
            requests.get("https://dolphin-trends.onrender.com/products", timeout=10)
        except:
            pass
        time.sleep(600)

def send_whatsapp(image_url, name, price):
    try:
        url = "https://api.green-api.com/waInstance" + GREEN_API_ID + "/sendFileByUrl/" + GREEN_API_TOKEN
        caption = "New Arrival!\n\n" + name + "\nPrice: " + price + "\n\nShop: " + FRONTEND_URL
        payload = {
            'chatId': WHATSAPP_NUMBER,
            'urlFile': image_url,
            'fileName': 'product.jpg',
            'caption': caption
        }
        response = requests.post(url, json=payload, timeout=30)
        print("WhatsApp: " + str(response.status_code))
    except Exception as e:
        print("WhatsApp Error: " + str(e))

def clean_text(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\S+', '', text)
    text = text.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
    return text.strip()

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "Photo received! AI analyzing...")

    try:
        caption = message.caption or ""
        price = "499"
        original_price = "799"

        for line in caption.split('\n'):
            if 'price:' in line.lower():
                price = line.split(':')[1].strip().replace("₹", "").replace("Rs.", "")
            if 'original:' in line.lower():
                original_price = line.split(':')[1].strip().replace("₹", "").replace("Rs.", "")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = "https://api.telegram.org/file/bot" + TELEGRAM_TOKEN + "/" + file_info.file_path
        photo_response = requests.get(file_url)
        image_bytes = photo_response.content

        # Gemini AI
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        image = Image.open(io.BytesIO(image_bytes))

        prompt = """Analyze this women's clothing photo for Dolphin Trends store.
Respond in exact JSON format only:
{
  "name": "short product name",
  "category": "ONE from: Tops, Leggings, Kurthas, Jeans, Patela Pants, Sets, Umbrella Dress, Frocks, Gym Pants",
  "description": "2 sentence English description",
  "dress_details": "describe dress colors and style briefly"
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
        dress_details = clean_text(ai_data.get("dress_details", "elegant dress"))

        bot.reply_to(message, "AI done! Generating model photo...")

        # Pollinations AI image
        ai_prompt = "beautiful young Indian woman perfect face full body shot wearing " + dress_details + " white studio background fashion photography photorealistic"
        formatted_prompt = requests.utils.quote(clean_text(ai_prompt))
        pollinations_url = "https://image.pollinations.ai/prompt/" + formatted_prompt + "?width=768&height=1024&seed=42&nologo=true&model=flux"

        img_response = requests.get(pollinations_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)

        if img_response.status_code == 200 and len(img_response.content) > 1000:
            final_image = img_response.content
        else:
            final_image = image_bytes

        bot.reply_to(message, "Uploading to website...")

        files = {'file': ('image.jpg', final_image, 'image/jpeg')}
        data = {
            'name': name,
            'price': "Rs." + price,
            'original_price': "Rs." + original_price,
            'description': description,
            'category': category
        }

        upload = requests.post(WEBSITE_URL, files=files, data=data, timeout=30)

        if upload.status_code == 200:
            try:
                image_url = upload.json().get('image', FRONTEND_URL)
            except:
                image_url = FRONTEND_URL

            send_whatsapp(image_url, name, "Rs." + price)
            bot.reply_to(message, "Successfully uploaded!\n\n" + name + "\nPrice: Rs." + price + "\nCategory: " + category + "\n\nWebsite: " + FRONTEND_URL)
        else:
            bot.reply_to(message, "Upload failed: " + upload.text)

    except Exception as e:
        bot.reply_to(message, "Error: " + str(e))

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Welcome to Dolphin Trends Bot!\n\nSend a photo with caption:\nPrice: 599\nOriginal: 999\n\nAI will generate name, category, description and model photo!")

if __name__ == "__main__":
    print("Starting Dolphin Bot...")
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    print("Bot polling started!")
    bot.polling(none_stop=True, timeout=60)
