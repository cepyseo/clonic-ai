import os
from flask import Flask, request
import telebot
import requests
import json

app = Flask(__name__)

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '7649208831:AAH3LX2zTvsmogWDn-gOhaGiC9lqD6q0MVk')
bot = telebot.TeleBot(BOT_TOKEN)

# OpenRouter API Key
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')

# Webhook URL
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://clonic-ai.onrender.com')

# Webhook kurulumu için endpoint
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    try:
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        # Önce mevcut webhook'u temizle
        bot.remove_webhook()
        # Yeni webhook'u ayarla
        response = bot.set_webhook(url=webhook_url)
        if response:
            return f'Webhook başarıyla ayarlandı! URL: {webhook_url}'
        else:
            return 'Webhook ayarlaması başarısız oldu!'
    except Exception as e:
        return f'Hata oluştu: {str(e)}'

# Start komutu için handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_message = (
            "👋 Merhaba! Ben bir görüntü analiz botuyum.\n\n"
            "🖼 Bana bir fotoğraf gönderdiğinizde, içeriğini analiz edip size açıklayacağım.\n\n"
            "📸 Hadi, bir fotoğraf göndererek başlayalım!"
        )
        bot.reply_to(message, welcome_message)
    except Exception as e:
        bot.reply_to(message, f"Bir hata oluştu: {str(e)}")

# Fotoğraf handler'ı
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # İşlem başladığını bildir
        processing_message = bot.reply_to(message, "🔄 Fotoğraf analiz ediliyor, lütfen bekleyin...")
        
        # Fotoğrafı al
        file_info = bot.get_file(message.photo[-1].file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        # OpenRouter API'ye istek gönder
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": WEBHOOK_URL,
                "X-Title": "TelegramImageAnalyzer",
            },
            json={
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What's in this image? Please describe in Turkish."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": photo_url
                                }
                            }
                        ]
                    }
                ]
            }
        )
        
        # İşlem mesajını sil
        bot.delete_message(message.chat.id, processing_message.message_id)
        
        # API yanıtını al ve kullanıcıya gönder
        result = response.json()
        analysis = result['choices'][0]['message']['content']
        bot.reply_to(message, f"🔍 Analiz Sonucu:\n\n{analysis}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Bir hata oluştu: {str(e)}")

# Webhook handler
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK'
    except Exception as e:
        return f'Error: {str(e)}'

# Ana sayfa
@app.route('/')
def home():
    return 'Bot aktif! 🤖'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)