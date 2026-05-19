import os
import requests
import asyncio
import threading
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# 1. ಸೆಟ್ಟಿಂಗ್ಸ್ ಮತ್ತು API ಕೀಗಳು
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = "8008263693:AAF9aYopkRzzjPf6VxYZ-oVtOr66UzffYUs"
WEBSITE_URL = "https://dolphin-trends.onrender.com/products"
FRONTEND_URL = "https://dolphin-frontend-mvke.onrender.com"

GREEN_API_ID = "7107622422"
GREEN_API_TOKEN = "615700ddddfc47b89c6a222ac5464dd45faec9e485a144d885"

client = genai.Client(api_key=GEMINI_API_KEY)
ai_photo_queue = []
is_loop_running = False
COOLDOWN_SECONDS = 15 * 60


# ------------------ 2. Website Alive ಇಡುವ ಫಂಕ್ಷನ್ ------------------
def keep_website_alive():
    while True:
        try:
            requests.get("https://dolphin-trends.onrender.com/products", timeout=10)
            requests.get(FRONTEND_URL, timeout=10)
            print("✅ Both websites are Alive!")
        except Exception as e:
            print(f"⚠️ Keep-alive error: {str(e)}")
        time.sleep(600)  # ಪ್ರತಿ 10 ನಿಮಿಷಕ್ಕೊಮ್ಮೆ ping


# ------------------ 3. WhatsApp ಶೇರಿಂಗ್ ಫಂಕ್ಷನ್ ------------------
def send_to_whatsapp_group(image_url):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendFileByUrl/{GREEN_API_TOKEN}"

    # ✅ Updated frontend URL
    caption = f"🛍️ *Dolphin Trends*\n👇 ಹೊಸ ಕಲೆಕ್ಷನ್ ನೋಡಿ! 👇\n🔗 {FRONTEND_URL}"

    payload = {
        'chatId': "917411255628@c.us",
        'urlFile': image_url,
        'fileName': 'product.jpg',
        'caption': caption
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"✅ WhatsApp Status: {response.status_code}")
        print(f"✅ WhatsApp Response: {response.text}")
        print(f"✅ Image URL Used: {image_url}")
    except Exception as e:
        print(f"❌ WhatsApp Error: {str(e)}")


# ------------------ 4. AI Queue ಪ್ರೊಸೆಸ್ ಫಂಕ್ಷನ್ ------------------
async def process_ai_queue(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    global is_loop_running, ai_photo_queue
    is_loop_running = True

    while len(ai_photo_queue) > 0:
        current_job = ai_photo_queue.pop(0)
        photo_bytes = current_job['photo_bytes']
        clean_title = current_job['title']

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ AI ಮೋಡ್: '{clean_title}' ಬಟ್ಟೆಗೆ ಮಾಡೆಲ್ ಶೂಟ್ ರೆಡಿ ಆಗ್ತಾ ಇದೆ..."
        )

        try:
            prompt_text = (
                "A high-fashion studio catalog style image of a beautiful young Indian model girl. "
                "She is wearing the exact same color, ethnic embroidery patterns, and suit design from the source image. "
                "Single frame split screen displaying exactly two stylish poses. Pure white background."
            )

            result = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt_text,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="3:4",
                    output_mime_type="image/jpeg",
                    person_generation="ALLOW_ADULT"
                )
            )

            final_bytes = result.generated_images[0].image.image_bytes
            description_text = (
                f"Premium beautiful {clean_title} featuring modern ethnic wear "
                f"designs with dual studio model poses."
            )

            files = {'file': ('product.jpg', final_bytes, 'image/jpeg')}
            data = {
                'name': clean_title,
                'price': '₹1200',
                'original_price': '₹1999',
                'description': description_text,
                'category': 'Sets'
            }

            web_response = requests.post(WEBSITE_URL, data=data, files=files, timeout=120)

            if web_response.status_code in [200, 201]:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ '{clean_title}' ವೆಬ್‌ಸೈಟ್‌ಗೆ ಅಪ್‌ಲೋಡ್ ಆಗಿದೆ!"
                )
                try:
                    web_data = web_response.json()
                    uploaded_image_url = web_data.get('image')
                    if not uploaded_image_url:
                        uploaded_image_url = FRONTEND_URL
                except Exception:
                    uploaded_image_url = FRONTEND_URL

                send_to_whatsapp_group(uploaded_image_url)

            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ ವೆಬ್‌ಸೈಟ್ ಅಪ್‌ಲೋಡ್ ಫೇಲ್: {web_response.status_code}"
                )

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ AI Error: {str(e)}"
            )

        if len(ai_photo_queue) > 0:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏳ ಮುಂದಿನ ಫೋಟೋಗೆ 15 ನಿಮಿಷಗಳ ಗ್ಯಾಪ್ ತಗೊಳ್ತಾ ಇದ್ದೀನಿ..."
            )
            await asyncio.sleep(COOLDOWN_SECONDS)

    is_loop_running = False


# ------------------ 5. Image Handler ಫಂಕ್ಷನ್ ------------------
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_photo_queue, is_loop_running

    user_caption = update.message.caption if update.message.caption else ""
    chat_id = update.message.chat_id

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    clean_title = user_caption.replace("#direct", "").strip()
    if not clean_title:
        clean_title = f"Dolphin Variant {datetime.now().strftime('%H%M%S')}"

    # ──────────── #direct ಮೋಡ್ ────────────
    if "#direct" in user_caption:
        direct_description = (
            f"Exclusive catalogue boutique item - {clean_title}. "
            f"Premium quality comfort fabric."
        )
        await update.message.reply_text(
            f"🚀 '{clean_title}' ಗೆ #direct ಇದೆ. ತಕ್ಷಣ ವೆಬ್‌ಸೈಟ್ ಮತ್ತು ವಾಟ್ಸಾಪ್‌ಗೆ ಕಳಿಸ್ತಾ ಇದ್ದೀನಿ..."
        )

        try:
            files = {'file': ('product.jpg', photo_bytes, 'image/jpeg')}
            data = {
                'name': clean_title,
                'price': '₹1200',
                'original_price': '₹1999',
                'description': direct_description,
                'category': 'Sets'
            }

            web_response = requests.post(WEBSITE_URL, data=data, files=files, timeout=120)

            if web_response.status_code in [200, 201]:
                await update.message.reply_text(f"✅ Direct Upload Success: '{clean_title}'!")

                try:
                    web_data = web_response.json()
                    uploaded_image_url = web_data.get('image')
                    if not uploaded_image_url:
                        uploaded_image_url = FRONTEND_URL
                except Exception:
                    uploaded_image_url = FRONTEND_URL

                send_to_whatsapp_group(uploaded_image_url)

            else:
                await update.message.reply_text(
                    f"❌ ವೆಬ್‌ಸೈಟ್ ಅಪ್‌ಲೋಡ್ ಫೇಲ್: {web_response.status_code}"
                )

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    # ──────────── AI ಮೋಡ್ ────────────
    else:
        ai_photo_queue.append({'photo_bytes': photo_bytes, 'title': clean_title})
        await update.message.reply_text(
            f"📥 '{clean_title}' ವೇಟಿಂಗ್ ಲಿಸ್ಟ್‌ಗೆ ಸೇರಿದೆ. "
            f"ಕ್ಯೂನಲ್ಲಿರೋ ಒಟ್ಟು ಫೋಟೋ: {len(ai_photo_queue)}"
        )
        if not is_loop_running:
            asyncio.create_task(process_ai_queue(context, chat_id))


# ------------------ 6. Main ------------------
def main():
    print("🚀 Bot successfully turned on! Now send photo on Telegram...")

    # ✅ Website sleep ಆಗದಂತೆ ತಡೆಯುತ್ತೆ
    threading.Thread(target=keep_website_alive, daemon=True).start()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.run_polling()


if __name__ == "__main__":
    main()