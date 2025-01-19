import os
from flask import Flask, request, jsonify
import telebot
import requests
import logging
from datetime import datetime
import json
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Logging ayarları
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Bot durumları için state yönetimi
class UserStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_language = State()
    waiting_for_style = State()

# Flask ve Bot kurulumu
app = Flask(__name__)
state_storage = StateMemoryStorage()
BOT_TOKEN = '7649208831:AAH3LX2zTvsmogWDn-gOhaGiC9lqD6q0MVk'
bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)

# OpenRouter API Ayarları
OPENROUTER_API_KEY = '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'

# Kullanıcı tercihlerini saklamak için dictionary
user_preferences = {}

def create_language_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    keyboard.row(
        InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
        InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")
    )
    return keyboard

def create_style_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🎨 Detaylı", callback_data="style_detailed"),
        InlineKeyboardButton("📝 Özet", callback_data="style_brief")
    )
    keyboard.row(
        InlineKeyboardButton("🎭 Eğlenceli", callback_data="style_fun"),
        InlineKeyboardButton("👔 Profesyonel", callback_data="style_professional")
    )
    return keyboard

def create_main_menu_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("📸 Fotoğraf Analizi", callback_data="analyze_photo"),
        InlineKeyboardButton("⚙️ Ayarlar", callback_data="settings")
    )
    keyboard.row(
        InlineKeyboardButton("ℹ️ Yardım", callback_data="help"),
        InlineKeyboardButton("📊 İstatistikler", callback_data="stats")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    logger.debug(f"Start command received from user {user_id}")
    
    # Kullanıcı tercihlerini başlat
    user_preferences[user_id] = {
        'language': 'tr',
        'style': 'detailed',
        'total_analyses': 0,
        'last_used': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    welcome_message = (
        "👋 Merhaba! Ben gelişmiş bir görüntü analiz botuyum.\n\n"
        "🔍 Yapabileceklerim:\n"
        "• 📸 Fotoğraf analizi\n"
        "• 🌍 Çoklu dil desteği\n"
        "• 🎨 Farklı analiz stilleri\n"
        "• 📊 Kullanım istatistikleri\n\n"
        "Başlamak için ana menüden bir seçim yapın!"
    )
    
    bot.reply_to(message, welcome_message, reply_markup=create_main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if call.data.startswith('lang_'):
        language = call.data.split('_')[1]
        user_preferences[user_id]['language'] = language
        bot.answer_callback_query(call.id, f"Dil tercihiniz kaydedildi: {language}")
        bot.edit_message_text(
            "Şimdi analiz stilini seçin:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_style_keyboard()
        )
    
    elif call.data.startswith('style_'):
        style = call.data.split('_')[1]
        user_preferences[user_id]['style'] = style
        bot.answer_callback_query(call.id, f"Stil tercihiniz kaydedildi: {style}")
        bot.edit_message_text(
            "✅ Ayarlarınız kaydedildi! Şimdi bir fotoğraf gönderebilirsiniz.",
            call.message.chat.id,
            call.message.message_id
        )
    
    elif call.data == 'analyze_photo':
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "📸 Lütfen analiz etmek istediğiniz fotoğrafı gönderin.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.set_state(user_id, UserStates.waiting_for_photo, call.message.chat.id)
    
    elif call.data == 'settings':
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "⚙️ Lütfen dilinizi seçin:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_language_keyboard()
        )
    
    elif call.data == 'help':
        help_text = (
            "🔍 *Nasıl Kullanılır:*\n\n"
            "1. Ayarlar menüsünden dilinizi ve analiz stilini seçin\n"
            "2. Bir fotoğraf gönderin\n"
            "3. Analiz sonucunu bekleyin\n\n"
            "📝 *Analiz Stilleri:*\n"
            "• Detaylı: Kapsamlı analiz\n"
            "• Özet: Kısa açıklama\n"
            "• Eğlenceli: Esprili anlatım\n"
            "• Profesyonel: Teknik detaylar\n\n"
            "❓ Sorunlarınız için: @YourSupportUsername"
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            help_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=create_main_menu_keyboard()
        )
    
    elif call.data == 'stats':
        if user_id in user_preferences:
            stats_text = (
                f"📊 *Kullanım İstatistikleriniz:*\n\n"
                f"🔍 Toplam Analiz: {user_preferences[user_id]['total_analyses']}\n"
                f"🌍 Tercih Edilen Dil: {user_preferences[user_id]['language']}\n"
                f"🎨 Analiz Stili: {user_preferences[user_id]['style']}\n"
                f"⏱ Son Kullanım: {user_preferences[user_id]['last_used']}"
            )
        else:
            stats_text = "❌ İstatistik bulunamadı."
            
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=create_main_menu_keyboard()
        )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    logger.debug(f"Photo received from user {user_id}")
    
    try:
        # İşlem başladığını bildir
        processing_msg = bot.reply_to(message, "🔄 Fotoğrafınız analiz ediliyor...")
        
        # Fotoğrafı al
        file_info = bot.get_file(message.photo[-1].file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        # Kullanıcı tercihlerine göre prompt oluştur
        language_prompts = {
            'tr': "Bu fotoğrafta ne var? Türkçe olarak açıkla.",
            'en': "What's in this image? Explain in English.",
            'de': "Was ist auf diesem Bild zu sehen? Auf Deutsch erklären.",
            'fr': "Qu'y a-t-il sur cette photo? Expliquer en français."
        }
        
        style_prompts = {
            'detailed': "Detaylı bir şekilde analiz et.",
            'brief': "Kısa ve öz bir şekilde açıkla.",
            'fun': "Eğlenceli ve espirili bir şekilde anlat.",
            'professional': "Profesyonel ve teknik bir dille açıkla."
        }
        
        user_lang = user_preferences.get(user_id, {}).get('language', 'tr')
        user_style = user_preferences.get(user_id, {}).get('style', 'detailed')
        
        prompt = f"{language_prompts[user_lang]} {style_prompts[user_style]}"
        
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
                            {"type": "text", "text": prompt},
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
        
        # İstatistikleri güncelle
        if user_id in user_preferences:
            user_preferences[user_id]['total_analyses'] += 1
            user_preferences[user_id]['last_used'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sonucu gönder
        bot.reply_to(
            message,
            f"🔍 *Analiz Sonucu:*\n\n{analysis}",
            parse_mode="Markdown",
            reply_markup=create_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error processing photo: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Üzgünüm, bir hata oluştu: {str(e)}\nLütfen tekrar deneyin.",
            reply_markup=create_main_menu_keyboard()
        )

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.debug(f"Message received from user {message.from_user.id}: {message.text}")
    bot.reply_to(
        message,
        "📸 Lütfen bir fotoğraf gönderin veya menüden bir seçim yapın!",
        reply_markup=create_main_menu_keyboard()
    )

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        logger.debug("Webhook request received")
        json_str = request.get_data().decode('UTF-8')
        logger.debug(f"Webhook data: {json_str}")
        
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK'
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_stats():
    return jsonify({
        'total_users': len(user_preferences),
        'total_analyses': sum(pref['total_analyses'] for pref in user_preferences.values()),
        'user_preferences': user_preferences
    })

@app.route('/')
def home():
    return 'Image Analysis Bot is running! 🤖'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)