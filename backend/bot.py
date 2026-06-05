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
        return response.status_code == 200
    except Exception as e:
        print("WhatsApp Error:", str(e))
        return False

# ================= INSTAGRAM AUTO-POST (SMART SESSION MODE) =================
def send_instagram_direct(image_bytes, name, category):
    # ⚡ [UPDATED]: ನಿನ್ನ ಇನ್‌ಸ್ಟಾಗ್ರಾಮ್ ಲಾಗಿನ್ ವಿವರಗಳನ್ನು ಇಲ್ಲಿ ಆಟೋಮ್ಯಾಟಿಕ್ ಸೆಟ್ ಮಾಡಲಾಗಿದೆ ಬಾಸ್
    INSTA_USERNAME = "7411255628"
    INSTA_PASSWORD = "9686609754"
    
    SESSION_FILE = "instagram_session.json"
    cl = Client()
    
    # ಕ್ರೋಮ್ ಬ್ರೌಸರ್ ಯೂಸರ್ ಏಜೆಂಟ್ ಸೆಟ್ ಮಾಡಲಾಗುತ್ತಿದೆ
    cl.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

    try:
        # 1. ಫಸ್ಟ್ ಸರ್ವರ್‌ನಲ್ಲಿ ಆಲ್ರೆಡಿ ಸೆಷನ್ ಫೈಲ್ ಇದ್ಯಾ ಅಂತ ಚೆಕ್ ಮಾಡುತ್ತೆ
        if os.path.exists(SESSION_FILE):
            print("📸 ಹಳೇ ಸೆಷನ್ ಫೈಲ್ ಸಿಕ್ಕಿದೆ, ಅದರ ಮೂಲಕ ಲಾಗಿನ್ ಆಗ್ತಿದೆ...")
            cl.load_settings(SESSION_FILE)
            try:
                cl.get_timeline_feed() # ಸೆಷನ್ ಆಕ್ಟಿವ್ ಆಗಿದ್ಯಾ ಅಂತ ಚೆಕ್ ಮಾಡ್ತಿದೆ
                print("✅ ಹಳೇ ಸೆಷನ್ ಇನ್ನು ವರ್ಕಿಂಗ್ ಆಗಿದೆ ಬಾಸ್!")
            except Exception:
                print("⚠️ ಹಳೇ ಸೆಷನ್ ಎಕ್ಸ್‌ಪೈರ್ ಆಗಿದೆ, ಹೊಸದಾಗಿ ಲಾಗಿನ್ ಆಗ್ತಿದೆ...")
                cl.login(INSTA_USERNAME, INSTA_PASSWORD)
                cl.dump_settings(SESSION_FILE) # ಹೊಸ ಸೆಷನ್ ಸೇವ್ ಮಾಡ್ತಿದೆ
        else:
            # 2. ಫೈಲ್ ಇಲ್ಲದಿದ್ದರೆ ಫ್ರೆಶ್ ಆಗಿ ಲಾಗಿನ್ ಆಗಿ ಫೈಲ್ ಕ್ರಿಯೇಟ್ ಮಾಡುತ್ತೆ
            print(f"📸 {INSTA_USERNAME} ಖಾತೆಗೆ ಫ್ರೆಶ್ ಆಗಿ ಲಾಗಿನ್ ಆಗ್ತಿದೆ...")
            cl.login(INSTA_USERNAME, INSTA_PASSWORD)
            cl.dump_settings(SESSION_FILE)
            print("✅ ಹೊಸ ಸೆಷನ್ ಫೈಲ್ ಯಶಸ್ವಿಯಾಗಿ ಸರ್ವರ್‌ನಲ್ಲಿ ಕ್ರಿಯೇಟ್ ಆಗಿದೆ ಬಾಸ್!")

        caption = (
            f"✨ {name}\n\n"
            f"Exclusive collection from Dolphin Trends. ✨\n\n"
            f"#dolphintrends #womensfashion #bangaloreshopping #kurti #trending"
        )

        temp_path = "temp_insta.jpg"
        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        print("🚀 Instagram ಗೆ ಫೋಟೋ ಅಪ್ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...")
        time.sleep(3)
        cl.photo_upload(temp_path, caption=caption)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        print("✅ Instagram ನಲ್ಲಿ ಸಕ್ಸಸ್‌ಫುಲ್ ಆಗಿ ಪೋಸ್ಟ್ ಆಗಿದೆ!")
        return True

    except Exception as e:
        print("❌ Instagram ಲಾಗಿನ್/ಪೋಸ್ಟ್ ಎರರ್:", str(e))
        if os.path.exists("temp_insta.jpg"):
            os.remove("temp_insta.jpg")
        return False

# ================= TELEGRAM BOT =================
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN ಮಿಸ್ ಆಗಿದೆ ಬಾಸ್!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "✅ Dolphin Trends Bot Ready!")

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
                price = line.split(':')[1].strip().replace("₹", "").replace("Rs.", "").strip()
            if 'original:' in line.lower():
                original_price = line.split(':')[1].strip().replace("₹", "").replace("Rs.", "").strip()

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"

        photo_response = requests.get(file_url)
        image_bytes = photo_response.content

        final_image = image_bytes
        name = "Dolphin Fashion"
        category = "Sets"
        description = "Premium fashion collection from Dolphin Trends"

        if is_direct:
            bot.reply_to(message, "⚡ Direct upload mode!")
            clean_caption = caption.replace("#direct", "").strip()
            for part in ["Price:", "Original:", "price:", "original:"]:
                clean_caption = clean_caption.split(part)[0].strip()
            if clean_caption:
                name = clean_caption
        else:
            bot.reply_to(message, "🤖 AI analyzing image...")
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY)
                image_pil = Image.open(io.BytesIO(image_bytes))
                prompt = """Analyze this women's clothing photo. Respond ONLY in JSON:\n{\n  "name": "product name",\n  "category": "Sets",\n  "description": "short description",\n  "dress_details": "dress color and style"\n}"""
                response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt, image_pil])
                response_text = response.text.strip()
            except Exception:
                import google.generativeai as old_genai
                old_genai.configure(api_key=GEMINI_API_KEY)
                model = old_genai.GenerativeModel('gemini-1.5-flash-latest')
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

        bot.reply_to(message, "🚀 Uploading to website...")
        files = {'file': ('image.jpg', final_image, 'image/jpeg')}
        data = {'name': name, 'price': "Rs." + price, 'original_price': "Rs." + original_price, 'description': description, 'category': category}
        
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
