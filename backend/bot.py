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
from instagrapi import Client  # 📸 ಇನ್‌ಸ್ಟಾಗ್ರಾಮ್ ಆಟೋಮೇಷನ್ ಲೈಬ್ರರಿ

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

# ⚡ [ಇಲ್ಲಿ ಚೇಂಜ್ ಆಗಿದೆ]: ನಿನ್ನ Render Env ವೇರಿಯಬಲ್ ಹೆಸರಿಗೆ ತಕ್ಕಂತೆ TELEGRAM_BOT_TOKEN ಗೆ ಮ್ಯಾಚ್ ಮಾಡಲಾಗಿದೆ
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

UPLOAD_URL = "https://dolphin-trends-3.onrender.com/products" # ನಿನ್ನ main.py ನ ಅಪ್ಲೋಡ್ URL ಗೆ ಮ್ಯಾಚ್ ಮಾಡಲಾಗಿದೆ
FRONTEND_URL = "https://dolphin-trends-two.vercel.app"

GREEN_API_ID = os.environ.get("GREEN_API_INSTANCE", "") # main.py ನ ಹೆಸರಿಗೆ ಮ್ಯಾಚ್ ಮಾಡಲಾಗಿದೆ
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("YOUR_WHATSAPP_GROUP_ID", "120363293847291048@g.us")

# 🔒 INSTAGRAM SETTINGS
INSTA_USER = os.environ.get("INSTAGRAM_USERNAME", "")
INSTA_PASS = os.environ.get("INSTAGRAM_PASSWORD", "")

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
        return response.status_code == 200

    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= INSTAGRAM AUTO-POST (NO PRICE & NO LINK) =================

def send_instagram_direct(image_bytes, name, category):
    if not INSTA_USER or not INSTA_PASS:
        print("⚠️ Instagram Username ಅಥವಾ Password ಎನ್ವಿರಾನ್ಮೆಂಟ್‌ನಲ್ಲಿ ಸೆಟ್ ಮಾಡಿಲ್ಲ!")
        return False

    try:
        print("📸 Instagrapi ಮೂಲಕ Instagram ಗೆ ಲಾಗಿನ್ ಆಗ್ತಿದೆ...")
        cl = Client()
        
        session_file = "insta_session.json"
        if os.path.exists(session_file):
            try:
                cl.load_settings(session_file)
                cl.login(INSTA_USER, INSTA_PASS)
            except Exception:
                cl.login(INSTA_USER, INSTA_PASS)
                cl.dump_settings(session_file)
        else:
            cl.login(INSTA_USER, INSTA_PASS)
            cl.dump_settings(session_file)

        # ✨ ಯಾವುದೇ ಬೆಲೆ (Price) ಮತ್ತು ಲಿಂಕ್ ಇಲ್ಲದ ಪ್ಯೂರ್ ಫ್ಯಾಷನ್ ಕ್ಯಾಪ್ಶನ್
        caption = (
            f"✨ {name}\n\n"
            f"Exclusive collection from Dolphin Trends. ✨\n\n"
            f"#dolphintrends #womensfashion #bangaloreshopping #kurti #trending"
        )

        temp_path = "temp_insta.jpg"
        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        print("🚀 Instagram ಗೆ ಫೋಟೋ ಅಪ್ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...")
        cl.photo_upload(temp_path, caption=caption)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        print("✅ Instagram ನಲ್ಲಿ ಆಟೋಮ್ಯಾಟಿಕ್ ಆಗಿ پೋಸ್ಟ್ ಆಗಿದೆ!")
        return True

    except Exception as e:
        print("❌ Instagrapi Error:", str(e))
        if os.path.exists("temp_insta.jpg"):
            os.remove("temp_insta.jpg")
        return False

# ================= TELEGRAM BOT =================

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN ಮಿಸ್ ಆಗಿದೆ ಬಾಸ್! Render Env ಚೆಕ್ ಮಾಡು.")

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
            
            # ಹೊಸ Google GenAI ಲೈಬ್ರರಿ ಬಳಸುವ ವಿಧಾನ
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY)
                image_pil = Image.open(io.BytesIO(image_bytes))

                prompt = """Analyze this women's clothing photo. Respond ONLY in JSON:
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
            except Exception:
                # ಒಂದು ವೇಳೆ ಹಳೇ ಲೈಬ್ರರಿ ಇಂಪೋರ್ಟ್ ಆಗಿದ್ರೆ ಬ್ಯಾಕಪ್ ವಿಧಾನ:
                import google.generativeai as old_genai
                old_genai.configure(api_key=GEMINI_API_KEY)
                model = old_genai.GenerativeModel('gemini-1.5-flash')
                image_pil = Image.open(io.BytesIO(image_bytes))
                response = model.generate_content(["Provide product name, category, and description in JSON format matching women clothing.", image_pil])
                response_text = response.text.strip()

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            try:
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
            except:
                pass

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

        if upload.status_code in [200, 201]:
            wa_success = send_whatsapp(final_image, name, "Rs." + price)
            insta_success = send_instagram_direct(final_image, name, category)

            status_msg = f"✅ Website Upload successful!\n"
            status_msg += f"{'📲 WhatsApp: Sent! ✅' if wa_success else '⚠️ WhatsApp: Failed ❌'}\n"
            status_msg += f"{'📸 Instagram: Posted! ✅' if insta_success else '⚠️ Instagram: Failed ❌'}\n\n"
            status_msg += f"🛍️ {name}\n💰 Rs.{price}\n📂 {category}\n\n🌐 {FRONTEND_URL}"

            bot.reply_to(message, status_msg)
        else:
            bot.reply_to(message, f"❌ Upload failed\nStatus: {upload.status_code}")

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
