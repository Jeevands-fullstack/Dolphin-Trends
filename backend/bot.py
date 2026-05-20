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

WEBSITE_URL = "https://dolphin-trends-2.onrender.com"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

GREEN_API_ID = os.environ.get("GREEN_API_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")

# WhatsApp Number
# Group Example: 120363xxxx@g.us
# Personal Example: 91xxxxxxxxxx@c.us
WHATSAPP_NUMBER = "917411255628@c.us"

# ================= FLASK =================

flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Dolphin Bot is Live!", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))

    flask_app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )

# ================= KEEP ALIVE =================

def keep_alive():

    while True:

        try:

            requests.get(
                "https://dolphin-trends.onrender.com/products",
                timeout=10
            )

            print("Website alive")

        except Exception as e:

            print("Keep alive error:", e)

        time.sleep(600)

# ================= CLEAN TEXT =================

def clean_text(text):

    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\S+', '', text)

    text = text.replace("[", "")
    text = text.replace("]", "")

    text = text.replace("(", "")
    text = text.replace(")", "")

    return text.strip()

# ================= WHATSAPP =================

def send_whatsapp(image_url, name, price):

    try:

        url = (
            "https://api.green-api.com/waInstance"
            + GREEN_API_ID +
            "/sendFileByUrl/" +
            GREEN_API_TOKEN
        )

        caption = (
            "🛍️ Dolphin Trends\n\n"
            + name +
            "\n💰 Price: " + price +
            "\n\n🌐 Shop Now:\n" +
            FRONTEND_URL
        )

        payload = {
            'chatId': WHATSAPP_NUMBER,
            'urlFile': image_url,
            'fileName': 'product.jpg',
            'caption': caption
        }

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        print("WhatsApp Status:", response.status_code)
        print(response.text)

    except Exception as e:

        print("WhatsApp Error:", str(e))

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

        print("Caption:", caption)
        print("Direct Mode:", is_direct)

        # ================= PRICE =================

        price = "499"
        original_price = "799"

        for line in caption.split('\n'):

            if 'price:' in line.lower():

                price = (
                    line.split(':')[1]
                    .strip()
                    .replace("₹", "")
                    .replace("Rs.", "")
                )

            if 'original:' in line.lower():

                original_price = (
                    line.split(':')[1]
                    .strip()
                    .replace("₹", "")
                    .replace("Rs.", "")
                )

        # ================= DOWNLOAD IMAGE =================

        file_id = message.photo[-1].file_id

        file_info = bot.get_file(file_id)

        file_url = (
            f"https://api.telegram.org/file/bot"
            f"{TELEGRAM_TOKEN}/"
            f"{file_info.file_path}"
        )

        photo_response = requests.get(file_url)

        image_bytes = photo_response.content

        # =====================================================
        # DIRECT MODE
        # =====================================================

        if is_direct:

            bot.reply_to(
                message,
                "⚡ Direct upload mode activated!"
            )

            clean_caption = (
                caption
                .replace("#direct", "")
                .replace("Price:", "")
                .replace("Original:", "")
                .strip()
            )

            if clean_caption == "":
                clean_caption = "Dolphin Fashion"

            name = clean_caption

            category = "Sets"

            description = (
                "Premium fashion collection from Dolphin Trends"
            )

            final_image = image_bytes

        # =====================================================
        # AI MODE
        # =====================================================

        else:

            bot.reply_to(
                message,
                "🤖 AI analyzing image..."
            )

            from google import genai

            client = genai.Client(
                api_key=GEMINI_API_KEY
            )

            image = Image.open(
                io.BytesIO(image_bytes)
            )

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

            # ================= CLEAN JSON =================

            if "```json" in response_text:

                response_text = (
                    response_text
                    .split("```json")[1]
                    .split("```")[0]
                    .strip()
                )

            elif "```" in response_text:

                response_text = (
                    response_text
                    .split("```")[1]
                    .split("```")[0]
                    .strip()
                )

            ai_data = json.loads(response_text)

            name = ai_data.get(
                "name",
                "Fashion Item"
            )

            category = ai_data.get(
                "category",
                "Sets"
            )

            description = ai_data.get(
                "description",
                "Beautiful fashion item"
            )

            dress_details = clean_text(
                ai_data.get(
                    "dress_details",
                    "beautiful traditional dress"
                )
            )

            bot.reply_to(
                message,
                "🎨 Generating AI model image..."
            )

            # ================= AI IMAGE =================

            ai_prompt = (
                "beautiful young Indian woman wearing "
                + dress_details +
                ", white background, studio fashion photography"
            )

            formatted_prompt = requests.utils.quote(
                clean_text(ai_prompt)
            )

            pollinations_url = (
                "https://image.pollinations.ai/prompt/"
                + formatted_prompt +
                "?width=768"
                "&height=1024"
                "&seed=42"
                "&nologo=true"
                "&model=flux"
            )

            img_response = requests.get(
                pollinations_url,
                headers={
                    'User-Agent': 'Mozilla/5.0'
                },
                timeout=60
            )

            if (
                img_response.status_code == 200
                and len(img_response.content) > 1000
            ):

                final_image = img_response.content

            else:

                print("AI image failed. Using original image.")

                final_image = image_bytes

        # =====================================================
        # WEBSITE UPLOAD
        # =====================================================

        bot.reply_to(
            message,
            "🚀 Uploading to website..."
        )

        files = {
            'file': (
                'image.jpg',
                final_image,
                'image/jpeg'
            )
        }

        data = {
            'name': name,
            'price': "Rs." + price,
            'original_price': "Rs." + original_price,
            'description': description,
            'category': category
        }

        upload = requests.post(
            WEBSITE_URL,
            files=files,
            data=data,
            timeout=60
        )

        print("UPLOAD STATUS:", upload.status_code)
        print("UPLOAD RESPONSE:", upload.text)

        # =====================================================
        # SUCCESS
        # =====================================================

        if upload.status_code in [200, 201]:

            try:

                upload_json = upload.json()

                image_url = (
                    upload_json.get("image")
                    or FRONTEND_URL
                )

            except:

                image_url = FRONTEND_URL

            # ================= WHATSAPP =================

            send_whatsapp(
                image_url,
                name,
                "Rs." + price
            )

            bot.reply_to(
                message,
                "✅ Successfully uploaded!\n\n"
                f"🛍️ {name}\n"
                f"💰 Price: Rs.{price}\n"
                f"📂 Category: {category}\n\n"
                f"🌐 {FRONTEND_URL}"
            )

        else:

            bot.reply_to(
                message,
                "❌ Upload failed\n\n"
                + upload.text
            )

    except Exception as e:

        print("ERROR:", str(e))

        bot.reply_to(
            message,
            "❌ Error:\n" + str(e)
        )

# ================= MAIN =================

if __name__ == "__main__":

    print("Starting Dolphin Bot...")

    # Flask Thread
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    # Keep Alive Thread
    threading.Thread(
        target=keep_alive,
        daemon=True
    ).start()

    # Remove old webhook
    bot.remove_webhook()

    time.sleep(2)

    # Polling Loop
    while True:

        try:

            print("Bot polling started!")

            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60
            )

        except Exception as e:

            print("Polling Error:", e)

            time.sleep(10)
