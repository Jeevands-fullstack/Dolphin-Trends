import os
import requests
import base64
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= SETTINGS =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
GREEN_API_ID = os.environ.get("GREEN_API_INSTANCE", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("YOUR_WHATSAPP_GROUP_ID", "120363293847291048@g.us")
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

# ================= WHATSAPP (Base64 Method) =================
def send_whatsapp(image_bytes, name, description):
    try:
        # ✅ Image base64 ಗೆ convert ಮಾಡಿ
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
        
        response = requests.post(url, json=payload, timeout=60)
        print(f"✅ WhatsApp sent! Status: {response.status_code}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ WhatsApp Error: {str(e)}")
        return False

# ================= TELEGRAM BOT =================
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 🔥 1. CRITICAL ADDITION: ಈಗಾಗಲೇ ಒಮ್ಮೆ ಕ್ಲಿಕ್ ಆಗಿರುವ ಬಟನ್‌ಗಳನ್ನು ಇಗ್ನೋರ್ ಮಾಡುವ ಹ್ಯಾಂಡ್ಲರ್
@bot.callback_query_handler(func=lambda call: call.data.startswith('clicked_'))
def handle_already_clicked(call):
    try:
        # ಟೆಲಿಗ್ರಾಮ್ ಲೋಡಿಂಗ್ ಸ್ಪಿನ್ನರ್ ಸ್ಟಾಪ್ ಮಾಡಿ ಸಣ್ಣ ಪಾಪ್-ಅಪ್ ಅಲರ್ಟ್ ತೋರಿಸುತ್ತದೆ
        bot.answer_callback_query(
            call.id, 
            text="This action is already processed! ⚠️", 
            show_alert=False
        )
    except Exception as e:
        print(f"❌ Error handling already clicked callback: {e}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # ✅ User ಗೆ confirmation ಕಳಿಸಿ
        bot.reply_to(message, "📥 Processing your product...")
        
        # ✅ ಅತಿ ದೊಡ್ಡ photo ಪಡೆಯಿರಿ
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        
        # ✅ Photo bytes download ಮಾಡಿ
        downloaded_file = bot.download_file(file_info.file_path)
        
        # ✅ Product name & description (ಇಲ್ಲಿ AI ಅಥವಾ default)
        product_name = "Premium Boutique Dress"
        product_description = "Beautiful designer wear with premium quality fabric."
        
        # ✅ Caption ಇದ್ದರೆ ಅದನ್ನು ಬಳಸಿ
        if message.caption:
            product_name = message.caption.strip()
        
        # ✅ WhatsApp ಗೆ ಕಳಿಸಿ
        success = send_whatsapp(downloaded_file, product_name, product_description)
        
        if success:
            bot.reply_to(message, "✅ Product uploaded and WhatsApp notification sent!")
        else:
            bot.reply_to(message, "⚠️ WhatsApp send failed. Please check logs.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

# ================= START BOT =================
if __name__ == "__main__":
    print("🤖 Bot starting...")
    print(f"📱 Telegram Token: {'✅ Set' if TELEGRAM_TOKEN else '❌ Missing'}")
    print(f"📱 Green API ID: {'✅ Set' if GREEN_API_ID else '❌ Missing'}")
    print(f"📱 Green API Token: {'✅ Set' if GREEN_API_TOKEN else '❌ Missing'}")
    print(f"📱 WhatsApp Number: {WHATSAPP_NUMBER}")
    print("🚀 Bot is polling...")
    bot.infinity_polling()
