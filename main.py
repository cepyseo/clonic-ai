import os
from flask import Flask, request
import telebot
import requests
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask ve Bot kurulumu
app = Flask(__name__)
BOT_TOKEN = '7649208831:AAH3LX2zTvsmogWDn-gOhaGiC9lqD6q0MVk'
bot = telebot.TeleBot(BOT_TOKEN)

# OpenRouter API Key
OPENROUTER_API_KEY = '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'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Merhaba! Ben bir görüntü analiz botuyum.\n\n"
        "📸 Bana bir fotoğraf gönderdiğinizde, içeriğini analiz edip size açıklayacağım.\n\n"
        "Hadi başlayalım! Bir fotoğraf gönderin."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # İşlem başladığını bildir
        processing_msg = bot.reply_to(message, "🔄 Fotoğrafınız analiz ediliyor...")
        
        # Fotoğrafı al
        file_info = bot.get_file(message.photo[-1].file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        # OpenRouter API'ye istek gönder
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://your-render-app-url.onrender.com",
                "X-Title": "TelegramImageAnalyzer",
            },
            json={
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Bu fotoğrafta ne var? Türkçe olarak detaylı açıkla."},
                            {"type": "image_url", "image_url": {"url": photo_url}}
                        ]
                    }
                ]
            }
        )
        
        # İşlem mesajını sil
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # Sonucu işle ve gönder
        result = response.json()
        analysis = result['choices'][0]['message']['content']
        bot.reply_to(message, f"🔍 Analiz Sonucu:\n\n{analysis}")
        
    except Exception as e:
        logger.error(f"Error processing photo: {str(e)}")
        bot.reply_to(message, f"❌ Üzgünüm, bir hata oluştu: {str(e)}\nLütfen tekrar deneyin.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "📸 Lütfen bir fotoğraf gönderin!")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK'

@app.route('/')
def home():
    return 'Bot aktif! 🤖'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))