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
TELEGRAM_TOKEN = os.environ.get("8008263693:AAF9aYopkRzzjPf6VxYZ-oVtOr66UzffYUs", "")
GEMINI_API_KEY = os.environ.get("AIzaSyCc-t9liV1MT1yjgGoQYn_hjrYSkuoMpy8", "")

WEBSITE_URL = https://dolphin-trends.onrender.com/upload-from-bot"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

GREEN_API_ID = os.environ.get("7107622422", "")
GREEN_API_TOKEN = os.environ.get("615700ddddfc47b89c6a222ac5464dd45faec9e485a144d885", "")

# WhatsApp group example:
# "1203633xxxxx@g.us"
# Personal:
# "91xxxxxxxxxx@c.us"
WHATSAPP_NUMBER = os.environ.get("917411255628@c.us", "")

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
            requests.get("https://dolphin-trends.onrender.com/products", timeout=10)
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
        url = (
            "https://api.green-api.com/waInstance"
            + GREEN_API_ID +
            "/sendFileByUrl/" +
            GREEN_API_TOKEN
        )

        caption = (
            "🛍️ Dolphin Trends\n\n"
            + name +
            "\nPrice: " + price +
            "\n\nShop Now:\n" +
            FRONTEND_URL
        )

        payload = {
            'chatId': WHATSAPP_NUMBER,
            'urlFile': image_url,
            'fileName': 'product.jpg',
            'caption': caption
        }

        response = requests.post(url, json=payload, timeout=30)

        print("WhatsApp Status:", response.status_code)
        print(response.text)

    except Exception as e:
        print("WhatsApp Error:", str(e))

# ================= TELEGRAM BOT =================
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(
        message,
        "✅ Dolphin Trends Bot Ready!\n\n"
        "Normal AI Mode:\n"
        "Send photo normally\n\n"
        "Direct Upload Mode:\n"
        "Send:\n"
        "Blue Kurti #direct"
    )

# ================= PHOTO HANDLER =================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):

    try:
        caption = message.caption or ""
        is_direct = "#direct" in caption.lower()

        print("CAPTION:", caption)
        print("DIRECT MODE:", is_direct)

        bot.reply_to(message, "📥 Photo received...")

        # ===== PRICE =====
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

        # ===== DOWNLOAD IMAGE =====
        file_id = message.photo[-1].file_id

        file_info = bot.get_file(file_id)

        file_url = (
            "https://api.telegram.org/file/bot"
            + TELEGRAM_TOKEN +
            "/" +
            file_info.file_path
        )

        photo_response = requests.get(file_url)

        image_bytes = photo_response.content

        # =====================================================
        # DIRECT MODE
        # =====================================================
        if is_direct:

            bot.reply_to(message, "⚡ Direct upload mode activated!")

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
                model='gemini-2.0-flash',
                contents=[prompt, image]
            )

            response_text = response.text.strip()

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

            name = ai_data.get("name", "Fashion Item")

            category = ai_data.get("category", "Sets")

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

            bot.reply_to(message, "🎨 Generating AI model image...")

            # ===== AI MODEL IMAGE =====
            ai_prompt = (
                "beautiful young Indian woman "
                "wearing " + dress_details +
                ", white background, studio fashion photography"
            )

            formatted_prompt = requests.utils.quote(
                clean_text(ai_prompt)
            )

            pollinations_url = (
                "https://image.pollinations.ai/prompt/"
                + formatted_prompt +
                "?width=768&height=1024"
                "&seed=42"
                "&nologo=true"
                "&model=flux"
            )

            img_response = requests.get(
                pollinations_url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=60
            )

            if (
                img_response.status_code == 200
                and len(img_response.content) > 1000
            ):
                final_image = img_response.content
            else:
                final_image = image_bytes

        # =====================================================
        # WEBSITE UPLOAD
        # =====================================================
        bot.reply_to(message, "🚀 Uploading to website...")

        files = {
            'file': ('image.jpg', final_image, 'image/jpeg')
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
        print(upload.text)

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

            # ===== WHATSAPP =====
            send_whatsapp(
                image_url,
                name,
                "Rs." + price
            )

            bot.reply_to(
                message,
                "✅ Successfully uploaded!\n\n"
                + "🛍️ " + name +
                "\n💰 Price: Rs." + price +
                "\n📂 Category: " + category +
                "\n\n🌐 " + FRONTEND_URL
            )

        else:

            bot.reply_to(
                message,
                "❌ Upload failed\n\n" + upload.text
            )

    except Exception as e:

        print("ERROR:", str(e))

        bot.reply_to(
            message,
            "❌ Error:\n" + str(e)
        )

# ================= MAIN =================
if __name__ == "__main__":

    print("🚀 Starting Dolphin Bot...")

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    threading.Thread(
        target=keep_alive,
        daemon=True
    ).start()

    print("🤖 Bot polling started!")

    bot.polling(
        none_stop=True,
        timeout=60
    )
