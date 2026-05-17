import os
import telebot
import requests
from google import genai
from google.genai import types
from PIL import Image
import io
import json
import re

# ─────────────────────────────────────────────────────────────────
# 🔑 ಕಾನ್ಫಿಗರೇಶನ್‌ಗಳು (Tokens & URLs)
# ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8008263693:AAF9aYopkRzzjPf6VxYZ-oVtOr66UzffYUs"
BACKEND_URL = "https://dolphin-trends.onrender.com"

# 🔐 ಸುರಕ್ಷಿತವಾಗಿ ಎನ್ವಿರಾನ್ಮೆಂಟ್ ಇಂದ ಕೀ ತಗೊಳ್ಳುವುದು
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY ಸಿಕ್ಕಿಲ್ಲ! ಟರ್ಮಿನಲ್‌ನಲ್ಲಿ ಕೀ ಸೆಟ್ ಮಾಡಿ.")

# ಹೊಸ ಜೆಮಿನಿ ಕ್ಲೈಂಟ್ ಇನಿಶಿಯಲೈಸೇಶನ್
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # ಕೀ ಇದೆಯಾ ಇಲ್ವಾ ಅಂತ ಮತ್ತೊಮ್ಮೆ ಚೆಕ್ ಮಾಡುವುದು
        if not os.environ.get("GEMINI_API_KEY"):
            bot.reply_to(message, "❌ Error: API Key ಸೆಟ್ ಮಾಡಿಲ್ಲ. ದಯವಿಟ್ಟು ಟರ್ಮಿನಲ್ ಪರಿಶೀಲಿಸಿ.")
            return

        # 1. ಟೆಲಿಗ್ರಾಮ್ ಕ್ಯಾಪ್ಶನ್‌ನಿಂದ ಬೆಲೆಯನ್ನು ಪಡೆದುಕೊಳ್ಳುವುದು
        caption = message.caption or ""
        price = ""
        original_price = ""

        for line in caption.split('\n'):
            if 'Price:' in line.strip() or 'price:' in line.strip():
                price = line.split(':')[1].strip().replace("₹", "")
            if 'Original:' in line.strip() or 'original:' in line.strip():
                original_price = line.split(':')[1].strip().replace("₹", "")

        # 2. ಟೆಲಿಗ್ರಾಮ್ ಸರ್ವರ್‌ನಿಂದ ಫೋಟೋ ಡೌನ್‌ಲೋಡ್ ಮಾಡುವುದು
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        photo_response = requests.get(file_url)
        image_bytes = photo_response.content

        bot.reply_to(message, "🤖 AI ಫೋಟೋ ವಿಶ್ಲೇಷಣೆ ಮತ್ತು ಇಂಗ್ಲಿಷ್ ಡಿಸ್ಕ್ರಿಪ್ಷನ್ ಬರೆಯುತ್ತಿದೆ...")

        # ಇಮೇಜ್ ಆಬ್ಜೆಕ್ಟ್ ಸಿದ್ಧಪಡಿಸುವುದು
        image = Image.open(io.BytesIO(image_bytes))

        # 3. ಜೆಮಿನಿ ಸ್ಟ್ರಿಕ್ಟ್ ಇಂಗ್ಲಿಷ್ ಪ್ರಾಂಪ್ಟ್
        prompt = """This is a clothing photo for 'Dolphin Trends', Bangalore. 
Please analyze it carefully and provide a response in the exact JSON format specified below.

Strict Rules for Analysis:
1. Product Name: Provide a short, trendy, and elegant English name.
2. Category: Choose EXACTLY ONE from: Tops, Leggings, Kurthas, Jeans, Patela Pants, Sets, Umbrella Dress, Frocks, Gym Pants.
3. Description: Write an attractive 2-sentence description STRICTLY in English only. Do not use Kannada.
4. Image Prompt Generation: Write a highly detailed description of THIS SPECIFIC dress for an AI image generator (describe color, fabric, style). Add this rule: 'The model must wear the exact same dress. Beautiful Indian woman giving 2 professional stylish studio poses, combined into a single wide banner image with a pure solid white background'.

Respond in this exact JSON format only, do not include markdown blocks like ```json:
{
  "name": "product name here",
  "category": "category here",
  "description": "description here",
  "ai_image_prompt": "highly detailed description text here"
}"""

        # ಜಿಮಿನಿ ಮಾಡೆಲ್ ಕಾಲ್
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )

        response_text = response.text.strip()

        # JSON ಡೇಟಾ ಫಿಲ್ಟರ್ ಮಾಡುವುದು
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        ai_data = json.loads(response_text)
        name = ai_data.get("name", "Dolphin Fashion Item")
        category = ai_data.get("category", "Tops")
        description = ai_data.get("description", "New arrivals at Dolphin Trends")
        ai_image_prompt = ai_data.get("ai_image_prompt", f"A beautiful Indian woman wearing a {name} shirt, white background")

        # 💡 ಫುಲ್ ಪ್ರೂಫ್ ಕ್ಲೀನಿಂಗ್: ಪ್ರಾಂಪ್ಟ್ ಒಳಗೆ ಯಾವುದೇ ಲಿಂಕ್‌ಗಳು, ಬ್ರಾಕೆಟ್‌ಗಳು ಅಥವಾ ಮಾರ್ಕ್‌ಡೌನ್ ಇದ್ದರೆ ಪೂರ್ತಿಯಾಗಿ ಡಿಲೀಟ್ ಮಾಡೋ ಲಾಜಿಕ್
        clean_prompt = re.sub(r'http\S+', '', ai_image_prompt) # ಎಂತಹುದೇ URL ಇದ್ದರೂ ರಿಮೂವ್ ಮಾಡುತ್ತೆ
        clean_prompt = clean_prompt.replace("[", "").replace("]", "").replace("(", "").replace(")", "").replace("'", "").replace('"', "")
        
        # ಡಿಫಾಲ್ಟ್ ಬೆಲೆ ಸೆಟ್ಟಿಂಗ್ಸ್
        if not price:
            price = "499"
        if not original_price:
            original_price = str(int(price) + 300)

        bot.reply_to(message, f"✨ AI Details Ready (In English)!\n\n🛍️ {name}\n📁 Category: {category}\n📝 {description}\n\n🎨 ಈಗ ಉಚಿತವಾಗಿ ಸುಂದರವಾದ AI ಮಾಡೆಲ್ ಇಮೇಜ್ ರೆಡಿ ಮಾಡಲಾಗುತ್ತಿದೆ...")

        # 4. Pollinations AI (ಉಚಿತ API) ಮೂಲಕ ವೈಟ್ ಬ್ಯಾಕ್‌ಗ್ರೌಂಡ್ ಫೋಟೋ ಜನರೇಟ್ ಮಾಡುವುದು
        formatted_prompt = requests.utils.quote(clean_prompt.strip())
        pollinations_url = f"[https://image.pollinations.ai/p/](https://image.pollinations.ai/p/){formatted_prompt}?width=1200&height=800&seed=45"
        
        print(f"Generating Free AI Image with URL: {pollinations_url}")
        
        # ಅಪ್ಪಿತಪ್ಪಿ ಯಾವುದೇ ತಪ್ಪು ಕ್ಯಾರೆಕ್ಟರ್ಸ್ ಇದ್ದರೂ requests ಸೇಫ್ ಆಗಿ ರನ್ ಆಗಲು ಹೆಡರ್ಸ್ ಸೆಟ್ ಮಾಡಲಾಗಿದೆ
        headers = {'User-Agent': 'Mozilla/5.0'}
        img_response = requests.get(pollinations_url, headers=headers)
        
        if img_response.status_code == 200 and len(img_response.content) > 1000:
            final_image_bytes = img_response.content
            print("AI image successfully downloaded!")
        else:
            final_image_bytes = image_bytes
            print("Failed to generate free AI image, falling back to original.")

        bot.reply_to(message, "🌐 ವೆಬ್‌ಸೈಟ್‌ಗೆ ಹೊಸ AI ಇಮೇಜ್ ಮತ್ತು ಇಂಗ್ಲಿಷ್ ಡಿಸ್ಕ್ರಿಪ್ಷನ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...")

        # 5. ನಿಮ್ಮ FastAPI ವೆಬ್‌ಸೈಟ್‌ಗೆ ಅಪ್‌ಲೋಡ್ ಮಾಡುವುದು
        files = {'file': ('image.jpg', final_image_bytes, 'image/jpeg')}
        data = {
            'name': name,
            'price': f"₹{price}",
            'original_price': f"₹{original_price}",
            'description': description,
            'category': category
        }

        upload_response = requests.post(
            BACKEND_URL + "/products",
            files=files,
            data=data
        )

        if upload_response.status_code == 200:
            bot.reply_to(message, f"✅ Successfully Uploaded to Website!\n\n🌐 Website: Updated with English details & Beautiful AI Model Image! 🚀")
        else:
            bot.reply_to(message, f"❌ Website upload failed: {upload_response.text}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Welcome to Dolphin Trends Bot!\n\nಬಟ್ಟೆಯ ಫೋಟೋ ಹಾಕಿ, AI ತಾನಾಗಿಯೇ ವೈಟ್ ಬ್ಯಾಕ್‌ಗ್ರೌಂಡ್ ಇರೋ ಸುಂದರ ಮಾಡೆಲ್ ಫೋಟೋ ಮತ್ತು ಇಂಗ್ಲಿಷ್ ಡಿಸ್ಕ್ರಿಪ್ಷನ್ ಕ್ರಿಯೇಟ್ ಮಾಡಿ ವೆಬ್‌ಸೈಟ್‌ಗೆ ಅಪ್‌ಲೋಡ್ ಮಾಡುತ್ತದೆ! 🐬")

print("Dolphin Trends Bot starting...")
bot.polling(none_stop=True)