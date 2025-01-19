import os
from flask import Flask, request
import telebot
import requests

app = Flask(__name__)
BOT_TOKEN = '7649208831:AAH3LX2zTvsmogWDn-gOhaGiC9lqD6q0MVk'
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Merhaba! Bana bir fotoğraf gönder, analiz edeyim!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer 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",
                "HTTP-Referer": "https://your-render-app-url.onrender.com",
                "X-Title": "TelegramImageAnalyzer",
            },
            json={
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What's in this image?"},
                            {"type": "image_url", "image_url": {"url": photo_url}}
                        ]
                    }
                ]
            }
        )
        
        result = response.json()
        analysis = result['choices'][0]['message']['content']
        bot.reply_to(message, analysis)
        
    except Exception as e:
        bot.reply_to(message, f"Hata: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Lütfen bir fotoğraf gönderin!")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK'

@app.route('/')
def home():
    return 'Bot çalışıyor!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))