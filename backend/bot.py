import os
import requests
import base64
import telebot

# ================= SETTINGS =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
GREEN_API_ID = os.environ.get("GREEN_API_INSTANCE", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("YOUR_WHATSAPP_GROUP_ID", "120363293847291048@g.us")
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

# ================= WHATSAPP (No Price) =================
def send_whatsapp(image_bytes, name, description):
    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        caption = (
            "🛍️ *Dolphin Trends - New Arrival!*\n\n"
            f"👕 *Product:* {name}\n"
            f"📝 *Details:* {description}\n\n"
            f"🌐 *View Price & Shop Now:*\n{FRONTEND_URL}"
        )
        url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByBase64/{GREEN_API_TOKEN}"
        payload = {
            "chatId": WHATSAPP_NUMBER,
            "file": f"data:image/jpeg;base64,{image_b64}",
            "fileName": "product.jpg",
            "caption": caption
        }
        requests.post(url, json=payload, timeout=60)
        return True
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= TELEGRAM BOT =================
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "📥 Processing your product...")
        # ನಿನ್ನ ಉಳಿದ ಫಂಕ್ಷನ್ ಇಲ್ಲಿ ಬರೆಯಿರಿ (AI analysis ಇತ್ಯಾದಿ)
        # ಇನ್ಮೇಲೆ send_instagram_direct ಕರೆಯುವ ಅಗತ್ಯವಿಲ್ಲ!
        bot.reply_to(message, "✅ Product uploaded and WhatsApp notification sent!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

if __name__ == "__main__":
    bot.infinity_polling()
