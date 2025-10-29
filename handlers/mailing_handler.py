import html
import re
from datetime import datetime
from telebot import types
from utils.helpers import extract_message_data, format_post_preview, is_admin


def setup_mailing_handlers(bot, db, scheduler):
    """Настройка обработчиков рассылок"""


    bot.temp_mailing_data = {}

    @bot.message_handler(commands=['mailing'])
    def mailing_command(message):
        """Рассылка подписчикам (только для админов)"""
        user = message.from_user

        if not is_admin(user.username):
            bot.reply_to(message, "❌ <b>У вас нет прав для отправки рассылок.</b>", parse_mode='HTML')
            return


        if not message.reply_to_message and len(message.text.split()) <= 1:
            show_mailing_examples(message)
            return

        message_text, image_url, parse_mode = extract_message_data(message)

        if not message_text and not image_url:
            bot.reply_to(message,
                         "❌ <b>Нечего отправлять в рассылке.</b>\n\n"
                         "💡 <b>Используйте один из способов:</b>\n"
                         "• Напишите текст после команды /mailing\n"
                         "• Ответьте на сообщение с текстом командой /mailing\n"
                         "• Ответьте на фото командой /mailing\n\n"
                         "📝 <b>Пример:</b> <code>/mailing Важное уведомление! 🚨</code>",
                         parse_mode='HTML'
                         )
            return

        ask_mailing_schedule(message, message_text, image_url, parse_mode)

    def show_mailing_examples(message):
        """Показать примеры использования команды /mailing"""
        examples_text = """
<b>📧 КАК ОТПРАВИТЬ РАССЫЛКУ:</b>

<u>Способ 1: Текст после команды</u>
<code>/mailing Важное уведомление для всех подписчиков! 📢</code>

<u>Способ 2: Ответ на сообщение</u>
1. Напишите текст сообщения
2. Ответьте на него командой <code>/mailing</code>

<u>Способ 3: Ответ на фото</u>
1. Отправьте фото (можно с подписью)
2. Ответьте на фото командой <code>/mailing</code>

<b>🎨 ФОРМАТИРОВАНИЕ ТЕКСТА:</b>
• <b>Жирный текст</b> - *жирный* или <b>жирный</b>
• <i>Курсив</i> - _курсив_ или <i>курсив</i>
• 🔥 Эмодзи поддерживаются!

<b>📋 ПРИМЕРЫ РАССЫЛОК:</b>

<code>/mailing *Специальное предложение!* 🎁
Только для наших подписчиков скидка 20%!
Успейте до конца недели! ⏳</code>

<code>/mailing <b>Новости проекта</b> 🚀
Рады сообщить о запуске новых функций!
Подробности по ссылке: example.com</code>
        """

        bot.reply_to(message, examples_text, parse_mode='HTML')

    def ask_mailing_schedule(message, message_text, image_url, parse_mode):
        """Спросить когда отправлять рассылку"""
        subscribers_count = len(db.get_all_subscribers())

        markup = types.InlineKeyboardMarkup()
        btn_now = types.InlineKeyboardButton("🚀 Отправить сейчас", callback_data="mailing_now")
        btn_schedule = types.InlineKeyboardButton("📅 Запланировать", callback_data="mailing_schedule")

        markup.row(btn_now, btn_schedule)

        preview = format_post_preview(message_text)

        ask_text = f"""
<b>📧 Рассылка готова к отправке:</b>

{preview}

👥 <b>Получателей:</b> {subscribers_count}

<b>Выберите действие:</b>
• <b>🚀 Отправить сейчас</b> - рассылка уйдет всем подписчикам сразу
• <b>📅 Запланировать</b> - рассылка будет отправлена в указанное время
        """


        sent_message = bot.send_message(
            message.chat.id,
            ask_text,
            reply_markup=markup,
            parse_mode='HTML'
        )


        mailing_key = f"{sent_message.chat.id}:{sent_message.message_id}"
        bot.temp_mailing_data[mailing_key] = {
            'message_text': message_text,
            'image_url': image_url,
            'parse_mode': parse_mode,
            'user_id': message.from_user.id,
            'original_message_id': sent_message.message_id
        }

    @bot.callback_query_handler(func=lambda call: call.data.startswith('mailing_'))
    def handle_mailing_callback(call):
        """Обработка нажатий на кнопки рассылок"""
        mailing_key = f"{call.message.chat.id}:{call.message.message_id}"

        if mailing_key not in bot.temp_mailing_data:
            bot.answer_callback_query(call.id, "❌ Данные рассылки устарели. Создайте рассылку заново.")
            return

        mailing_data = bot.temp_mailing_data[mailing_key]
        message_text = mailing_data['message_text']
        image_url = mailing_data['image_url']
        parse_mode = mailing_data['parse_mode']

        if call.data == "mailing_schedule":
            handle_schedule_mailing(call, message_text, image_url, parse_mode, mailing_key)

        elif call.data == "mailing_now":
            handle_send_mailing_now(call, message_text, image_url, parse_mode, mailing_key)

    def handle_schedule_mailing(call, message_text, image_url, parse_mode, mailing_key):
        """Обработка кнопки 'Запланировать' для рассылки"""
        schedule_help_text = """
<b>📅 ЗАПЛАНИРОВАТЬ РАССЫЛКУ</b>

<u>Формат даты и времени:</u>
<code>ГГГГ-ММ-ДД ЧЧ:ММ</code>

<u>Примеры:</u>
• <code>2024-12-25 09:00</code> - 25 декабря 2024 в 09:00
• <code>2024-12-31 18:00</code> - 31 декабря 2024 в 18:00
• <code>2025-01-01 12:00</code> - 1 января 2025 в 12:00

👇 <b>Введите дату и время в указанном формате:</b>
        """

        bot.edit_message_text(
            schedule_help_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )

        bot.temp_mailing_data[mailing_key]['waiting_for_schedule'] = True

        bot.register_next_step_handler_by_chat_id(
            call.message.chat.id,
            process_mailing_schedule_time,
            message_text,
            image_url,
            parse_mode,
            mailing_key
        )

        bot.answer_callback_query(call.id, "📅 Введите дату и время для рассылки")

    def process_mailing_schedule_time(message, message_text, image_url, parse_mode, mailing_key):
        """Обработка ввода времени для планирования рассылки"""
        try:
            if message.text.startswith('/'):
                bot.reply_to(message, "❌ <b>Планирование рассылки отменено.</b>", parse_mode='HTML')
                cleanup_mailing_data(bot, mailing_key)
                return

            scheduled_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            now = datetime.now()

            if scheduled_time <= now:
                bot.reply_to(message,
                             "❌ <b>Указанное время уже прошло.</b>\n\n"
                             "Используйте будущую дату и время.",
                             parse_mode='HTML'
                             )
                cleanup_mailing_data(bot, mailing_key)
                return

            subscribers_count = len(db.get_all_subscribers())

            post_id = db.add_mailing_post(message.from_user.username, message_text, image_url,
                                          scheduled_time.isoformat())

            scheduler.schedule_mailing_post(post_id, message_text, image_url, scheduled_time, parse_mode)

            success_text = f"""
<b>✅ Рассылка запланирована!</b>

📝 <b>Превью:</b> {format_post_preview(message_text, 80)}
📅 <b>Дата отправки:</b> {scheduled_time.strftime('%d.%m.%Y %H:%M')}
👥 <b>Получателей:</b> {subscribers_count}
🆔 <b>ID рассылки:</b> {post_id}
👤 <b>Автор:</b> @{message.from_user.username or 'Неизвестно'}

💫 <b>Рассылка будет автоматически отправлена всем подписчикам в указанное время!</b>
            """

            bot.reply_to(message, success_text, parse_mode='HTML')

            cleanup_mailing_data(bot, mailing_key)

        except ValueError:
            error_text = """
❌ <b>Неверный формат даты/времени!</b>

<u>Правильный формат:</u>
<code>ГГГГ-ММ-ДД ЧЧ:ММ</code>

<u>Примеры правильного ввода:</u>
• <code>2024-12-25 09:00</code>
• <code>2024-12-31 18:00</code>
• <code>2025-01-01 12:00</code>

👇 <b>Попробуйте еще раз:</b>
            """

            bot.reply_to(message, error_text, parse_mode='HTML')
            bot.register_next_step_handler(
                message,
                process_mailing_schedule_time,
                message_text,
                image_url,
                parse_mode,
                mailing_key
            )
        except Exception as e:
            print(f"Ошибка планирования рассылки: {e}")
            bot.reply_to(message, "❌ <b>Ошибка при планировании рассылки.</b>", parse_mode='HTML')
            cleanup_mailing_data(bot, mailing_key)

    def handle_send_mailing_now(call, message_text, image_url, parse_mode, mailing_key):
        """Обработка кнопки 'Отправить сейчас' для рассылки"""
        subscribers_count = len(db.get_all_subscribers())

        if subscribers_count == 0:
            bot.edit_message_text(
                "❌ <b>Нет подписчиков для рассылки.</b>\n\n"
                "Пока никто не подписался на бота через /start",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            cleanup_mailing_data(bot, mailing_key)
            return


        bot.edit_message_text(
            f"📤 <b>Начинаю рассылку для {subscribers_count} подписчиков...</b>\n\n"
            "⏳ <i>Это может занять несколько минут</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )


        success_count, fail_count = scheduler.send_broadcast(message_text, image_url, parse_mode)


        report_text = f"""
<b>📊 Отчет о рассылке:</b>

✅ <b>Успешно доставлено:</b> {success_count}
❌ <b>Не доставлено:</b> {fail_count}
👥 <b>Всего подписчиков:</b> {subscribers_count}

💫 <b>Эффективность:</b> {(success_count / subscribers_count * 100) if subscribers_count > 0 else 0:.1f}%
        """

        bot.edit_message_text(
            report_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )


        cleanup_mailing_data(bot, mailing_key)
        bot.answer_callback_query(call.id, f"✅ Рассылка отправлена: {success_count}/{subscribers_count}")

    def cleanup_mailing_data(bot, mailing_key):
        """Очистка временных данных рассылки"""
        if mailing_key in bot.temp_mailing_data:
            del bot.temp_mailing_data[mailing_key]

    @bot.message_handler(commands=['mailing_help'])
    def mailing_help_command(message):
        """Помощь по рассылкам"""
        show_mailing_examples(message)