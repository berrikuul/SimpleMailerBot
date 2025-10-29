import logging
import telebot
from config import BOT_TOKEN, GROUP_CHAT_ID
from database import Database
from utils.scheduler import SchedulerManager


from handlers.start_handler import setup_start_handlers
from handlers.post_handler import setup_post_handlers
from handlers.mailing_handler import setup_mailing_handlers
from handlers.admin_handler import setup_admin_handlers


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск бота...")

    try:
        bot = telebot.TeleBot(BOT_TOKEN)
        bot.group_chat_id = GROUP_CHAT_ID  # Добавляем ID группы в объект бота

        db = Database()
        scheduler = SchedulerManager(bot, db)

        scheduler.restore_scheduled_posts()

        setup_start_handlers(bot, db)
        setup_post_handlers(bot, db, scheduler)
        setup_mailing_handlers(bot, db, scheduler)
        setup_admin_handlers(bot, db, scheduler)

        @bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            help_text = """
<b>👋 Привет! Я бот для рассылок.</b>

💫 <b>Основные команды:</b>
/start - подписаться на рассылку
/help - помощь по командам
            """
            bot.reply_to(message, help_text, parse_mode='HTML')

        logger.info("✅ Бот успешно инициализирован")
        logger.info("🤖 Запускаю опрос сервера...")

        # Запуск бота
        bot.infinity_polling(timeout=60, long_polling_timeout=60)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        if 'scheduler' in locals():
            scheduler.shutdown()


if __name__ == '__main__':
    main()