#!/usr/bin/env python3
"""
Telegram Business Bot для Render.com
"""
import os
import re
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8589626698:AAG-I6zsLyrv8fhGqvstHoMgXvVWiBjvSh8")
USDT_RATE = 80.41

# Инициализация Flask и бота
app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)

def create_check_markup(amount):
    """Создаем кнопку для чека"""
    usdt_str = f"{amount:.1f}".rstrip('0').rstrip('.')
    
    keyboard = [[
        InlineKeyboardButton(
            f"Получить {usdt_str} USDT",
            callback_data=f"get_{usdt_str}"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Основной обработчик вебхука"""
    if request.method == "POST":
        try:
            # Получаем обновление
            update_data = request.get_json(force=True)
            update = telegram.Update.de_json(update_data, bot)
            
            logger.info(f"📨 Update ID: {update.update_id}")
            
            # Обработка сообщений
            if update.message and update.message.text:
                text = update.message.text
                chat_id = update.message.chat.id
                
                logger.info(f"💬 Сообщение: {text}")
                logger.info(f"👤 От: {update.message.from_user.username}")
                logger.info(f"🆔 Чат ID: {chat_id}")
                
                # Проверяем бизнес-сообщение
                if hasattr(update.message, 'business_connection_id'):
                    logger.info(f"⚡ БИЗНЕС! Connection ID: {update.message.business_connection_id}")
                
                # Обрабатываем команду .send usdt
                if text.lower().startswith('.send usdt'):
                    try:
                        parts = text.split()
                        if len(parts) >= 3:
                            amount = float(parts[2])
                            
                            # Рассчитываем сумму в рублях
                            rub = amount * USDT_RATE
                            
                            # Форматируем
                            usdt_str = f"{amount:.1f}".rstrip('0').rstrip('.')
                            rub_str = f"{rub:,.0f}".replace(',', ' ')
                            now = datetime.now().strftime("%H:%M")
                            
                            # Текст чека (как на скриншоте)
                            check_text = (
                                f"₽{usdt_str}\n"
                                f"{rub_str} ₽\n\n"
                                f"🔄 Чек на T {usdt_str} USDT ({rub_str} RUB).\n"
                                f"TeleGrom ↗️, {now}↘️\n\n"
                                f"Получить {usdt_str} USDT"
                            )
                            
                            # Отправляем чек
                            bot.send_message(
                                chat_id=chat_id,
                                text=check_text,
                                reply_markup=create_check_markup(amount),
                                reply_to_message_id=update.message.message_id
                            )
                            
                            logger.info(f"✅ Чек отправлен: {usdt_str} USDT")
                            
                    except Exception as e:
                        logger.error(f"❌ Ошибка обработки чека: {e}")
                        bot.send_message(
                            chat_id=chat_id,
                            text=f"❌ Ошибка: {str(e)}"
                        )
            
            # Обработка нажатий кнопок
            elif update.callback_query:
                query = update.callback_query
                query.answer()
                
                if query.data.startswith("get_"):
                    amount = query.data.replace("get_", "")
                    
                    # Редактируем сообщение
                    bot.edit_message_text(
                        chat_id=query.message.chat.id,
                        message_id=query.message.message_id,
                        text=f"✅ Заявка на {amount} USDT принята!\n"
                             f"Ожидайте перевод от @username"
                    )
                    
                    logger.info(f"🔄 Кнопка нажата: {amount} USDT")
            
            return jsonify({"status": "ok"})
            
        except Exception as e:
            logger.error(f"🔥 Ошибка в webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "method not allowed"}), 405

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Установка вебхука"""
    # Получаем домен Render
    render_domain = os.environ.get("RENDER_EXTERNAL_URL", request.host_url.rstrip('/'))
    webhook_url = f"{render_domain}/webhook"
    
    # Устанавливаем вебхук
    result = bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message", "callback_query", "business_message"]
    )
    
    return f"""
    <h1>🤖 Telegram Business Bot</h1>
    <p>Webhook установлен: {result}</p>
    <p>URL: {webhook_url}</p>
    <p>Бот: @{bot.get_me().username}</p>
    <hr>
    <p>Теперь:</p>
    <ol>
        <li>Настройте бота в Telegram Business → Chatbots</li>
        <li>Добавьте: @{bot.get_me().username}</li>
        <li>Выберите "All 1-to-1 chats"</li>
        <li>Напишите другу: <code>.send usdt 100</code></li>
    </ol>
    """

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    """Удаление вебхука"""
    result = bot.delete_webhook()
    return f"Webhook удален: {result}"

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья"""
    try:
        bot_info = bot.get_me()
        return jsonify({
            "status": "ok",
            "bot": bot_info.username,
            "webhook": bot.get_webhook_info().url
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    """Главная страница"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Telegram Business Bot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .card { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
            code { background: #333; color: #fff; padding: 2px 6px; border-radius: 4px; }
            a { color: #0088cc; }
        </style>
    </head>
    <body>
        <h1>🤖 Telegram Business Bot</h1>
        
        <div class="card">
            <h2>✅ Бот работает!</h2>
            <p>Ссылки для управления:</p>
            <ul>
                <li><a href="/set_webhook">Установить webhook</a></li>
                <li><a href="/delete_webhook">Удалить webhook</a></li>
                <li><a href="/health">Проверка здоровья</a></li>
            </ul>
        </div>
        
        <div class="card">
            <h2>📋 Инструкция</h2>
            <ol>
                <li>Настройте бота в <strong>Telegram Business → Chatbots</strong></li>
                <li>Введите username бота: <code>@{bot.get_me().username if 'bot' in locals() else 'ваш_бот'}</code></li>
                <li>Выберите "All 1-to-1 chats"</li>
                <li>Напишите другу: <code>.send usdt 100</code></li>
                <li>Бот отправит чек с кнопкой</li>
            </ol>
        </div>
        
        <div class="card">
            <h2>🔄 Команды</h2>
            <p><code>.send usdt 100</code> - отправить чек на 100 USDT</p>
            <p><code>.send usdt 50.5</code> - отправить чек на 50.5 USDT</p>
        </div>
        
        <footer>
            <p>Развернуто на <a href="https://render.com">Render.com</a></p>
        </footer>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Получаем порт из переменных окружения Render
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 60)
    print("🤖 TELEGRAM BUSINESS BOT")
    print("=" * 60)
    print(f"Токен: {TOKEN[:10]}...")
    print(f"Порт: {port}")
    print("=" * 60)
    print("\nДля установки webhook перейдите:")
    print("1. https://ВАШ-ПРОЕКТ.onrender.com/set_webhook")
    print("2. Или вручную: https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://ВАШ-ПРОЕКТ.onrender.com/webhook")
    print("=" * 60)
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=port, debug=False)