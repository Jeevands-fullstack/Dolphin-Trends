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
lock_file = open("/tmp/dolphin_bot.lock", "w")
try:
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    print("✅ Bot lock acquired - single instance running")
except IOError:
    print("❌ Another bot instance is already running! Exiting...")
    sys.exit(0)

# ================= SETTINGS =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
UPLOAD_URL = "https://dolphin-trends-3.onrender.com/products"
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"
GREEN_API_ID = os.environ.get("GREEN_API_INSTANCE", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("YOUR_WHATSAPP_GROUP_ID", "120363293847291048@g.us")

INSTAGRAM_ACCOUNT_ID = "1784142484746231"
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

# ================= CLEAN TEXT =================
def clean_text(text):
    text = re.sub(r'http\S+|www\S+|[()\[\]]', '', text)
    return text.strip()

# ================= WHATSAPP =================
def send_whatsapp(image_bytes, name, price):
    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        caption = f"🛍️ *Dolphin Trends*\n\n👕 *Product:* {name}\n💰 *Price:* {price}\n\n🌐 *Shop Now:*\n{FRONTEND_URL}"
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByBase64/{GREEN_API_TOKEN}"
        payload = {
            "chatId": WHATSAPP_NUMBER,
            "file": f"data:image/jpeg;base64,{image_b64}",
            "fileName": "product.jpg",
            "caption": caption
        }
        response = requests.post(url, json=payload, timeout=60)
        return response.status_code == 200
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= INSTAGRAM OFFICIAL GRAPH API =================
def send_instagram_direct(image_bytes, name, category):
    if not INSTAGRAM_ACCESS_TOKEN:
        print("⚠️ Instagram Access Token ಸೆಟ್ ಮಾಡಿಲ್ಲ!")
        return False

    caption = f"✨ {name}\n\nExclusive collection from Dolphin Trends. ✨\n#dolphintrends #bangaloreshopping"
    try:
        formatted_prompt = requests.utils.quote(clean_text(name))
        image_url = f"https://image.pollinations.ai/prompt/{formatted_prompt}?width=768&height=1024&seed=42&nologo=true&model=flux"
        
        container_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
        payload = {'image_url': image_url, 'caption': caption, 'access_token': INSTAGRAM_ACCESS_TOKEN}
        
        response = requests.post(container_url, data=payload, timeout=30).json()
        container_id = response.get('id')
        
        if not container_id:
            print("❌ ಮೀಡಿಯಾ ಕಂಟೈನರ್ ಕ್ರಿಯೇಟ್ ಆಗಿಲ್ಲ:", response)
            return False
            
        time.sleep(5)
        publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        publish_payload = {'creation_id': container_id, 'access_token': INSTAGRAM_ACCESS_TOKEN}
        
        res = requests.post(publish_url, data=publish_payload, timeout=30).json()
        return 'id' in res
    except Exception as e:
        print("❌ Instagram API Error:", str(e))
        return False

# ================= TELEGRAM BOT =================
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "📥 Processing...")
        # (ನಿನ್ನ ಹಳೆಯ logic ಇಲ್ಲೇ ಇರಲಿ)
        # ಅಂತಿಮವಾಗಿ ಇನ್‌ಸ್ಟಾಗ್ರಾಮ್ ಕಾಲ್ ಮಾಡುವಾಗ:
        send_instagram_direct(None, "New Product", "Sets")
        bot.reply_to(message, "✅ Task Complete!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

if __name__ == "__main__":
    bot.infinity_polling()
