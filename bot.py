import logging
import re
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    ContextTypes, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    CommandHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === КОНФИГУРАЦИЯ ===
TOKEN = "8589626698:AAG-I6zsLyrv8fhGqvstHoMgXvVWiBjvSh8"  # Ваш токен
WEBHOOK_URL = "https://ваш-домен.ру/webhook"  # НУЖЕН HTTPS!
PORT = 8443  # Или 443, 80, 88, 8443
HOST = "0.0.0.0"

# Курс
USDT_RATE = 80.41

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🤖 Business Bot активирован!\n"
        "Отправьте в ЛЮБОЙ чат: .send usdt 100"
    )

async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений из бизнес-чатов"""
    
    # Если нет текста - выходим
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    logger.info(f"Получено сообщение в бизнес-чате: {text}")
    
    # Проверяем команду .send usdt
    if text.lower().startswith('.send usdt'):
        try:
            # Извлекаем сумму
            parts = text.split()
            if len(parts) < 3:
                return
            
            amount = float(parts[2])
            
            # Рассчитываем рубли
            rub = amount * USDT_RATE
            
            # Форматируем
            usdt_str = f"{amount:.1f}".rstrip('0').rstrip('.')
            rub_str = f"{rub:,.0f}".replace(',', ' ')
            
            # Время
            now = datetime.now().strftime("%H:%M")
            
            # Текст чека (ТОЧНО как на скриншоте)
            check_text = (
                f"₽{usdt_str}\n"
                f"{rub_str} ₽\n\n"
                f"🔄 Чек на T {usdt_str} USDT ({rub_str} RUB).\n"
                f"TeleGrom ↗️, {now}↘️\n\n"
                f"Получить {usdt_str} USDT"
            )
            
            # Кнопка
            keyboard = [[
                InlineKeyboardButton(
                    f"Получить {usdt_str} USDT",
                    callback_data=f"get_{usdt_str}"
                )
            ]]
            
            # Отправляем чек
            await update.message.reply_text(
                text=check_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=None
            )
            
            logger.info(f"✅ Чек на {usdt_str} USDT отправлен")
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_"):
        amount = query.data.replace("get_", "")
        await query.edit_message_text(
            f"✅ Заявка на {amount} USDT принята!\n"
            f"Ожидайте перевод от администратора."
        )

async def main():
    """Запуск с Webhook (ОБЯЗАТЕЛЬНО для Business)"""
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_business_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # === ВАЖНО: НУЖЕН HTTPS ДОМЕН ===
    print("=" * 60)
    print("⚠️  Business-бот требует Webhook с HTTPS!")
    print(f"Токен: {TOKEN}")
    print("=" * 60)
    print("\nБыстрые варианты развертывания:")
    print("1. PythonAnywhere (бесплатно)")
    print("2. Heroku (бесплатно)")
    print("3. VPS с Nginx + SSL")
    print("4. ngrok для тестирования")
    print("=" * 60)
    
    # Запускаем polling ТОЛЬКО для теста
    # Для продакшена нужен Webhook!
    print("\n🚀 Запускаю в режиме polling для теста...")
    application.run_polling()

if __name__ == "__main__":
    main()