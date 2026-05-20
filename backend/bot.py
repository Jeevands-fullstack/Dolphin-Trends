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

# ================= SETTINGS =================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

BACKEND_BASE_URL = "https://dolphin-trends.onrender.com"
WEBSITE_URL = "https://dolphin-trends.onrender.com/products"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

GREEN_API_ID = os.environ.get("GREEN_API_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")

WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "917411255628@c.us")

# ================= FLASK =================

flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Dolphin Bot is Live!", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False)

# ================= KEEP ALIVE =================

def keep_alive():
    while True:
        try:
            requests.get(WEBSITE_URL, timeout=10)
            print("Website alive")
        except Exception as e:
            print("Keep alive error:", e)
        time.sleep(600)

# ================= CLEAN TEXT =================

def clean_text(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\S+', '', text)
    text = text.replace("[", "").replace("]", "")
    text = text.replace("(", "").replace(")", "")
    return text.strip()

# ================= WHATSAPP =================

def send_whatsapp(image_url, name, price):
    try:
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByUrl/{GREEN_API_TOKEN}"

        caption = (
            "🛍️ *Dolphin Trends*\n\n"
            f"👕 *Product:* {name}\n"
            f"💰 *Price:* {price}\n\n"
            f"🌐 *Shop Now:*\n{FRONTEND_URL}"
        )

        payload = {
            'chatId': WHATSAPP_NUMBER,
            'urlFile': image_url,
            'fileName': 'product.jpg',
            'caption': caption
        }

        print(f"📡 Sending to WhatsApp. URL: {url}")
        print(f"📡 Payload: {payload}")

        response = requests.post(url, json=payload, timeout=30)

        print("WhatsApp Status Code:", response.status_code)
        print("WhatsApp Server Response:", response.text)

        return response.status_code == 200

    except Exception as e:
        print("WhatsApp Exception Error:", str(e))
        return False

# ================= TELEGRAM BOT =================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ================= START COMMAND =================

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(
        message,
        "✅ Dolphin Trends Bot Ready!\n\n"
        "📸 Send product photo\n\n"
        "⚡ Direct Upload:\n"
        "Blue Kurti #direct"
    )

# ================= PHOTO HANDLER =================

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "📥 Photo received...")
        caption = message.caption or ""
        is_direct = "#direct" in caption.lower()

        price = "499"
        original_price = "799"

        for line in caption.split('\n'):
            if 'price:' in line.lower():
                price = line.split(':', 1)[1].strip().replace("₹", "").replace("Rs.", "")
            if 'original:' in line.lower():
                original_price = line.split(':', 1)[1].strip().replace("₹", "").replace("Rs.", "")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"

        photo_response = requests.get(file_url, timeout=30)
        image_bytes = photo_response.content

        final_image = image_bytes
        name = "Dolphin Fashion"
        category = "Sets"
        description = "Premium fashion collection from Dolphin Trends"
        backup_whatsapp_image = file_url

        # DIRECT MODE
        if is_direct:
            bot.reply_to(message, "⚡ Direct upload mode activated!")
            clean_caption = caption.replace("#direct", "").replace("Price:", "").replace("Original:", "").strip()
            if clean_caption == "":
                clean_caption = "Dolphin Fashion"
            name = clean_caption

        # AI MODE
        else:
            bot.reply_to(message, "🤖 AI analyzing image...")
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            image = Image.open(io.BytesIO(image_bytes))

            prompt = """
Analyze this women's clothing photo.
Respond ONLY in JSON:
{
  "name": "product name",
  "category": "Sets",
  "description": "short description",
  "dress_details": "dress color and style"
}
"""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt, image]
            )

            response_text = response.text.strip()

            if "```json" in response_text:
                response_text = response_text.split("```json").split("```").strip()[1]
            elif "```" in response_text:
                response_text = response_text.split("```")[11].split("```")[0].strip()

            ai_data = json.loads(response_text)
            name = ai_data.get("name", "Fashion Item")
            category = ai_data.get("category", "Sets")
            description = ai_data.get("description", "Beautiful fashion item")
            dress_details = clean_text(ai_data.get("dress_details", "beautiful traditional dress"))

            bot.reply_to(message, "🎨 Generating AI model image...")

            ai_prompt = f"beautiful young Indian woman wearing {dress_details}, white background, studio fashion photography"
            formatted_prompt = requests.utils.quote(clean_text(ai_prompt))

            pollinations_url = f"https://image.pollinations.ai/prompt/{formatted_prompt}?width=768&height=1024&seed=42&nologo=true&model=flux"

            img_response = requests.get(
                pollinations_url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=60
            )

            if img_response.status_code == 200 and len(img_response.content) > 1000:
                final_image = img_response.content
                backup_whatsapp_image = pollinations_url
            else:
                print("AI image failed. Using original image.")
                final_image = image_bytes
                backup_whatsapp_image = file_url

        # WEBSITE UPLOAD
        bot.reply_to(message, "🚀 Uploading to website...")

        files = {'file': ('image.jpg', final_image, 'image/jpeg')}
        data = {
            'name': name,
            'price': "Rs." + price,
            'original_price': "Rs." + original_price,
            'description': description,
            'category': category
        }

        upload = requests.post(WEBSITE_URL, files=files, data=data, timeout=60)
        print("UPLOAD STATUS:", upload.status_code)
        print("UPLOAD RESPONSE:", upload.text)

        if upload.status_code in [200, 201]:
            image_url = ""
            try:
                upload_json = upload.json()
                raw_image_path = upload_json.get("image") or upload_json.get("imageUrl") or upload_json.get("path") or ""
                if raw_image_path:
                    if raw_image_path.startswith("http"):
                        image_url = raw_image_path
                    else:
                        if not raw_image_path.startswith("/"):
                            raw_image_path = "/" + raw_image_path
                        image_url = f"{BACKEND_BASE_URL}{raw_image_path}"
            except Exception as e:
                print("JSON Parsing failed, using backup image:", e)

            if not image_url:
                image_url = backup_whatsapp_image

            print(f"🎯 Final WhatsApp Trigger URL: {image_url}")
            wa_ok = send_whatsapp(image_url, name, "Rs." + price)
            print("WhatsApp sent:", wa_ok)

            bot.reply_to(
                message,
                f"✅ Successfully uploaded!\n\n"
                f"🛍️ {name}\n"
                f"💰 Price: Rs.{price}\n"
                f"📂 Category: {category}\n\n"
                f"🌐 {FRONTEND_URL}"
            )
        else:
            bot.reply_to(message, f"❌ Upload failed\n\n{upload.text}")

    except Exception as e:
        print("ERROR:", str(e))
        bot.reply_to(message, "❌ Error:\n" + str(e))

# ================= MAIN =================

if __name__ == "__main__":
    print("Starting Dolphin Bot...")

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    try:
        print("Deleting webhook...")
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("Webhook delete error:", e)

    time.sleep(5)
    print("Bot polling started!")

    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Polling Error:", e)
