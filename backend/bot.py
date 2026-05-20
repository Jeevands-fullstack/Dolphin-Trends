 import os
import io
import json
import re
import base64
import requests
import time
import sys
import fcntl
from PIL import Image
import telebot

# ================= SINGLE INSTANCE LOCK =================
# Ee code multiple instances run aagodannu prevent madthade

lock_file = open("/tmp/dolphin_bot.lock", "w")
try:
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    print("✅ Bot lock acquired - single instance running")
except IOError:
    print("❌ Another bot instance is already running! Exiting...")
    sys.exit(0)

# ================= SETTINGS =================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

UPLOAD_URL = "https://dolphin-trends.onrender.com/upload-from-bot"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

GREEN_API_ID = os.environ.get("GREEN_API_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "917411255628@c.us")

# ================= CLEAN TEXT =================

def clean_text(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\S+', '', text)
    text = text.replace("[", "").replace("]", "")
    text = text.replace("(", "").replace(")", "")
    return text.strip()

# ================= WHATSAPP =================

def send_whatsapp(image_bytes, name, price):
    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        caption = (
            "🛍️ *Dolphin Trends*\n\n"
            f"👕 *Product:* {name}\n"
            f"💰 *Price:* {price}\n\n"
            f"🌐 *Shop Now:*\n{FRONTEND_URL}"
        )

        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByBase64/{GREEN_API_TOKEN}"

        payload = {
            "chatId": WHATSAPP_NUMBER,
            "file": f"data:image/jpeg;base64,{image_b64}",
            "fileName": "product.jpg",
            "caption": caption
        }

        print("📡 Sending to WhatsApp...")
        response = requests.post(url, json=payload, timeout=60)
        print("WhatsApp Status:", response.status_code)
        print("WhatsApp Response:", response.text)

        return response.status_code == 200

    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= TELEGRAM BOT =================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(
        message,
        "✅ Dolphin Trends Bot Ready!\n\n"
        "📸 Product photo kalsidre auto upload aagthade\n\n"
        "⚡ Direct mode: photo + caption alli #direct bari\n"
        "Example: Blue Kurti #direct"
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "📥 Photo received...")
        caption = message.caption or ""
        is_direct = "#direct" in caption.lower()

        # ================= PRICE =================
        price = "499"
        original_price = "799"

        for line in caption.split('\n'):
            if 'price:' in line.lower():
                price = line.split(':')[1].strip().replace("₹", "").replace("Rs.", "").strip()
            if 'original:' in line.lower():
                original_price = line.split(':')[1].strip().replace("₹", "").replace("Rs.", "").strip()

        # ================= DOWNLOAD IMAGE =================
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"

        photo_response = requests.get(file_url)
        image_bytes = photo_response.content

        final_image = image_bytes
        name = "Dolphin Fashion"
        category = "Sets"
        description = "Premium fashion collection from Dolphin Trends"

        # =====================================================
        # DIRECT MODE
        # =====================================================
        if is_direct:
            bot.reply_to(message, "⚡ Direct upload mode!")
            clean_caption = caption.replace("#direct", "").strip()
            for part in ["Price:", "Original:", "price:", "original:"]:
                clean_caption = clean_caption.split(part)[0].strip()
            if clean_caption:
                name = clean_caption

        # =====================================================
        # AI MODE
        # =====================================================
        else:
            bot.reply_to(message, "🤖 AI analyzing image...")
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            image_pil = Image.open(io.BytesIO(image_bytes))

            prompt = """Analyze this women's clothing photo.
Respond ONLY in JSON:
{
  "name": "product name",
  "category": "Sets",
  "description": "short description",
  "dress_details": "dress color and style"
}"""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt, image_pil]
            )

            response_text = response.text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            ai_data = json.loads(response_text)
            name = ai_data.get("name", "Fashion Item")
            category = ai_data.get("category", "Sets")
            description = ai_data.get("description", "Beautiful fashion item")
            dress_details = clean_text(ai_data.get("dress_details", "beautiful traditional dress"))

            bot.reply_to(message, "🎨 Generating AI model image...")

            ai_prompt = f"beautiful young Indian woman wearing {dress_details}, white background, studio fashion photography"
            formatted_prompt = requests.utils.quote(clean_text(ai_prompt))
            pollinations_url = f"https://image.pollinations.ai/prompt/{formatted_prompt}?width=768&height=1024&seed=42&nologo=true&model=flux"

            img_response = requests.get(pollinations_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)

            if img_response.status_code == 200 and len(img_response.content) > 1000:
                final_image = img_response.content
            else:
                final_image = image_bytes

        # =====================================================
        # UPLOAD TO BACKEND
        # =====================================================
        bot.reply_to(message, "🚀 Uploading to website...")

        files = {'file': ('image.jpg', final_image, 'image/jpeg')}
        data = {
            'name': name,
            'price': "Rs." + price,
            'original_price': "Rs." + original_price,
            'description': description,
            'category': category
        }

        upload = requests.post(UPLOAD_URL, files=files, data=data, timeout=60)
        print("UPLOAD STATUS:", upload.status_code)
        print("UPLOAD RESPONSE:", upload.text)

        if upload.status_code in [200, 201]:
            wa_success = send_whatsapp(final_image, name, "Rs." + price)

            if wa_success:
                bot.reply_to(
                    message,
                    f"✅ Upload successful!\n"
                    f"📲 WhatsApp message sent!\n\n"
                    f"🛍️ {name}\n"
                    f"💰 Rs.{price}\n"
                    f"📂 {category}\n\n"
                    f"🌐 {FRONTEND_URL}"
                )
            else:
                bot.reply_to(
                    message,
                    f"✅ Website upload successful!\n"
                    f"⚠️ WhatsApp send failed\n\n"
                    f"🛍️ {name}\n"
                    f"💰 Rs.{price}\n"
                    f"🌐 {FRONTEND_URL}"
                )
        else:
            bot.reply_to(message, f"❌ Upload failed\nStatus: {upload.status_code}\n{upload.text}")

    except Exception as e:
        print("ERROR:", str(e))
        bot.reply_to(message, "❌ Error:\n" + str(e))

# ================= MAIN =================

if __name__ == "__main__":
    print("🤖 Dolphin Bot Starting...")

    try:
        bot.remove_webhook()
    except:
        pass

    time.sleep(2)
    print("✅ Bot polling started!")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Polling Error:", e)
            time.sleep(10)
   
            
