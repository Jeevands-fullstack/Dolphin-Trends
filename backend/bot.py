import telebot
import requests
from google import genai
from google.genai import types
from PIL import Image
import io
import json

# ─────────────────────────────────────────────────────────────────
# 🔑 ಕಾನ್ಫಿಗರೇಶನ್‌ಗಳು (Tokens & URLs)
# ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8008263693:AAF9aYopkRzzjPf6VxYZ-oVtOr66UzffYUs"
GEMINI_API_KEY = "AIzaSyBFLtkqjnvlR9vYjJTkCMHcC-cOpm1TWzc"
BACKEND_URL = "https://dolphin-trends.onrender.com"

# ಹೊಸ ಜೆಮಿನಿ ಕ್ಲೈಂಟ್ ಇನಿಶಿಯಲೈಸೇಶನ್
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
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

        # 3. ಜೆಮಿನಿ ಪ್ರಾಂಪ್ಟ್ (ಕಂಪ್ಲೀಟ್ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ವಿವರಗಳನ್ನು ಪಡೆಯಲು ಮತ್ತು ಇಮೇಜ್ ಜನರೇಷನ್ ಪ್ರಾಂಪ್ಟ್ ಕ್ರಿಯೇಟ್ ಮಾಡಲು)
        prompt = """This is a clothing photo for 'Dolphin Trends', Bangalore. 
Please analyze it carefully and provide a response in the exact JSON format specified below.

Strict Rules for Analysis:
1. Product Name: Provide a short, trendy, and elegant English name.
2. Category: Choose EXACTLY ONE from: Tops, Leggings, Kurthas, Jeans, Patela Pants, Sets, Umbrella Dress, Frocks, Gym Pants.
3. Description: Write an attractive 2-sentence description STRICTLY in English only. Do not use Kannada.
4. Image Prompt Generation: Write a highly detailed text-to-image prompt for an AI generator. It must describe the exact color, fabric texture, buttons, collar, and pocket of THIS SPECIFIC dress. Add a rule: 'The model must wear the exact same dress without any changes to design or color. Subject must be a beautiful Indian woman giving 2 professional stylish studio poses, combined into a single wide banner image with a pure solid white background'.

Respond in this exact JSON format only, do not include markdown blocks like ```json:
{
  "name": "product name here",
  "category": "category here",
  "description": "description here",
  "ai_image_prompt": "highly detailed image generation prompt here"
}"""

        # ಜಿಮಿನಿ ಹೊಸ ಮಾಡೆಲ್ ಕಾಲ್
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )

        response_text = response.text.strip()

        # ಕ್ಲೀನ್ ಆಗಿ JSON ಡೇಟಾ ಮಾತ್ರ ಫಿಲ್ಟರ್ ಮಾಡುವುದು
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        ai_data = json.loads(response_text)
        name = ai_data.get("name", "Dolphin Fashion Item")
        category = ai_data.get("category", "Tops")
        description = ai_data.get("description", "New arrivals at Dolphin Trends")
        ai_image_prompt = ai_data.get("ai_image_prompt", f"A beautiful Indian woman wearing a {name} shirt, white background")

        # ಡಿಫಾಲ್ಟ್ ಬೆಲೆ ಸೆಟ್ಟಿಂಗ್ಸ್
        if not price:
            price = "499"
        if not original_price:
            original_price = str(int(price) + 300)

        bot.reply_to(message, f"✨ AI Details Ready (In English)!\n\n🛍️ {name}\n📁 Category: {category}\n📝 {description}\n\n🎨 ಈಗ ಉಚಿತವಾಗಿ ಸುಂದರವಾದ AI ಮಾಡೆಲ್ ಇಮೇಜ್ ರೆಡಿ ಮಾಡಲಾಗುತ್ತಿದೆ...")

        # 4. 🎨 Pollinations AI (ಉಚಿತ API) ಮೂಲಕ ವೈಟ್ ಬ್ಯಾಕ್‌ಗ್ರೌಂಡ್ ಫೋಟೋ ಜನರೇಟ್ ಮಾಡುವುದು
        formatted_prompt = requests.utils.quote(ai_image_prompt)
        pollinations_url = f"[https://image.pollinations.ai/p/](https://image.pollinations.ai/p/){formatted_prompt}?width=1200&height=800&seed=45"
        
        print("Generating free AI model image from Pollinations...")
        img_response = requests.get(pollinations_url)
        
        # ಯಶಸ್ವಿಯಾಗಿ ಫೋಟೋ ಜನರೇಟ್ ಆದ್ರೆ ಅದರ ಬೈಟ್ಸ್ ತಗೋಬೇಕು, ಇಲ್ಲದಿದ್ರೆ ಒರಿಜಿನಲ್ ಫೋಟೋ ಬಳಸಬೇಕು
        if img_response.status_code == 200:
            final_image_bytes = img_response.content
            print("AI image successfully generated!")
        else:
            final_image_bytes = image_bytes
            print("Failed to generate free AI image, falling back to original.")

        bot.reply_to(message, "🌐 ವೆಬ್‌ಸೈಟ್‌ಗೆ ಹೊಸ AI ಇಮೇಜ್ ಮತ್ತು ಇಂಗ್ಲಿಷ್ ಡಿಸ್ಕ್ರಿಪ್ಷನ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...")

        # 5. ನಿಮ್ಮ FastAPI ವೆಬ್‌ಸೈಟ್‌ಗೆ ಅಪ್‌ಲೋಡ್ ಮಾಡುವುದು (ಹೊಸ ಇಮೇಜ್ ಬೈಟ್ಸ್‌ನೊಂದಿಗೆ)
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

        # 6. ವಾಟ್ಸಾಪ್ ಕಂಪ್ಲೀಟ್ ಆಗಿ ಸ್ಕಿಪ್ ಮಾಡಲಾಗಿದೆ (Scam/Suspicious ಇಶ್ಯೂ ತಡೆಯಲು)
        whatsapp_sent = False 

        # 7. ಯಶಸ್ವಿಯಾದ ಸಂದೇಶ
        if upload_response.status_code == 200:
            status_msg = f"✅ Successfully Uploaded to Website!\n\n🌐 Website: Updated with English details & Beautiful AI Model Image! 🚀"
            bot.reply_to(message, status_msg)
        else:
            bot.reply_to(message, f"❌ Website upload failed but AI worked: {upload_response.text}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Welcome to Dolphin Trends Bot!\n\nಬಟ್ಟೆಯ ಫೋಟೋ ಹಾಕಿ, ಕ್ಯಾಪ್ಶನ್‌ನಲ್ಲಿ ಹೀಗೆ ಬರೆಯಿರಿ:\nPrice: 599\nOriginal: 999\n\nAI ತಾನಾಗಿಯೇ ವೈಟ್ ಬ್ಯಾಕ್‌ಗ್ರೌಂಡ್ ಇರೋ ಸುಂದರ ಮಾಡೆಲ್ ಫೋಟೋ ಮತ್ತು ಇಂಗ್ಲಿಷ್ ಡಿಸ್ಕ್ರಿಪ್ಷನ್ ಕ್ರಿಯೇಟ್ ಮಾಡಿ ವೆಬ್‌ಸೈಟ್‌ಗೆ ಅಪ್‌ಲೋಡ್ ಮಾಡುತ್ತದೆ! 🐬")

print("Dolphin Trends Bot starting with Free AI Model Generation...")
bot.polling(none_stop=True)