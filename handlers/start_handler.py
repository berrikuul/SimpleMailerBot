import html
from telebot import types
from config import GROUP_LINK


def setup_start_handlers(bot, db):
    """Настройка обработчиков команды /start"""

    @bot.message_handler(commands=['start'])
    def start_command(message):
        """Команда /start - подписка на рассылку"""
        user = message.from_user
        db.add_subscriber(user.id, user.username, user.first_name, user.last_name)

        markup = types.InlineKeyboardMarkup()
        join_button = types.InlineKeyboardButton(
            "🎯 Вступить в закрытое сообщество",
            url=GROUP_LINK
        )
        markup.add(join_button)

        welcome_text = f"""
<b>👋 Привет, {html.escape(user.first_name)}!</b>

🎉 Добро пожаловать в наш бот рассылок!

📢 <b>Здесь ты будешь получать:</b>
• Важные уведомления
• Эксклюзивные новости  
• Специальные предложения

💬 <b>Присоединяйся к нашему закрытому сообществу!</b>

⚡ <b>Доступные команды:</b>
/post - опубликовать пост в группу
/my_posts - мои запланированные посты
/help - помощь по командам
        """

        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    @bot.message_handler(commands=['help'])
    def help_command(message):
        """Команда /help - справка"""
        from utils.helpers import is_admin
        user = message.from_user
        is_user_admin = is_admin(user.username)

        help_text = """
<b>📋 Доступные команды:</b>

👤 <b>Для всех пользователей:</b>
/start - подписаться на рассылку
/post - опубликовать пост в группу
/my_posts - мои запланированные посты
/help - показать эту справку
        """

        if is_user_admin:
            help_text += """
👑 <b>Для администраторов:</b>
/mailing - отправить рассылку подписчикам
/scheduled - список всех запланированных постов
/cancel - отменить запланированный пост
/stats - статистика бота
            """

        help_text += """
<b>💡 Форматирование текста:</b>
• <b>Жирный текст</b> - *жирный* или <b>жирный</b>
• <i>Курсив</i> - _курсив_ или <i>курсив</i>
• 🔥 Эмодзи поддерживаются!

<b>🖼️ Отправка изображений:</b>
Ответьте на изображение командой /post или /mailing
        """

        bot.send_message(message.chat.id, help_text, parse_mode='HTML')