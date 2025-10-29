import html
import re
from datetime import datetime
from telebot import types
from utils.helpers import extract_message_data, format_post_preview
from config import GROUP_CHAT_ID


def setup_post_handlers(bot, db, scheduler):
    """Настройка обработчиков постов в группу"""

    # Временное хранилище для данных постов
    bot.temp_post_data = {}

    @bot.message_handler(commands=['post'])
    def post_command(message):
        """Публикация поста в группу"""

        if not message.reply_to_message and len(message.text.split()) <= 1:
            show_post_examples(message)
            return

        message_text, image_url, parse_mode = extract_message_data(message)

        if not message_text and not image_url:
            bot.reply_to(message,
                         "❌ <b>Нечего публиковать в посте.</b>\n\n"
                         "💡 <b>Используйте один из способов:</b>\n"
                         "• Напишите текст после команды /post\n"
                         "• Ответьте на сообщение с текстом командой /post\n"
                         "• Ответьте на фото командой /post\n\n"
                         "📝 <b>Пример:</b> <code>/post Привет всем! 👋</code>",
                         parse_mode='HTML'
                         )
            return

        ask_post_schedule(message, message_text, image_url, parse_mode)

    def show_post_examples(message):
        """Показать примеры использования команды /post"""
        examples_text = """
<b>📝 КАК СОЗДАТЬ ПОСТ:</b>

<u>Способ 1: Текст после команды</u>
<code>/post Всем привет! Сегодня отличный день! 🌞</code>

<u>Способ 2: Ответ на сообщение</u>
1. Напишите текст сообщения
2. Ответьте на него командой <code>/post</code>

<u>Способ 3: Ответ на фото</u>
1. Отправьте фото (можно с подписью)
2. Ответьте на фото командой <code>/post</code>

<u>Способ 4: Текст + ссылка на картинку</u>
<code>/post Смотрите новое фото! [img:https://example.com/photo.jpg]</code>

<b>🎨 ФОРМАТИРОВАНИЕ ТЕКСТА:</b>
• <b>Жирный текст</b> - *жирный* или <b>жирный</b>
• <i>Курсив</i> - _курсив_ или <i>курсив</i>
• 🔥 Эмодзи поддерживаются!

<b>📋 ПРИМЕРЫ ПОСТОВ:</b>

<code>/post *Важное объявление!* 📢
Сегодня в 18:00 состоится собрание.
Не пропустите! 🎯</code>

<code>/post <b>Новости проекта</b> 🚀
Рады сообщить о новых возможностях!
Подробности по ссылке: example.com</code>
        """

        bot.reply_to(message, examples_text, parse_mode='HTML')

    def ask_post_schedule(message, message_text, image_url, parse_mode):
        """Спросить когда публиковать пост"""
        markup = types.InlineKeyboardMarkup()
        btn_now = types.InlineKeyboardButton("🚀 Опубликовать сейчас", callback_data="post_now")
        btn_schedule = types.InlineKeyboardButton("📅 Запланировать", callback_data="post_schedule")

        markup.row(btn_now, btn_schedule)

        preview = format_post_preview(message_text)

        ask_text = f"""
    <b>📝 Ваш пост готов к публикации:</b>

    {preview}

    <b>Выберите действие:</b>
    • <b>🚀 Опубликовать сейчас</b> - пост сразу появится в группе
    • <b>📅 Запланировать</b> - пост будет опубликован в указанное время
        """

        sent_message = bot.send_message(
            message.chat.id,
            ask_text,
            reply_markup=markup,
            parse_mode='HTML'
        )

        post_key = f"{sent_message.chat.id}:{sent_message.message_id}"
        bot.temp_post_data[post_key] = {
            'message_text': message_text,
            'image_url': image_url,
            'user_id': message.from_user.id,
            'original_message_id': sent_message.message_id,
            'parse_mode': parse_mode
        }

    @bot.callback_query_handler(func=lambda call: call.data.startswith('post_'))
    def handle_post_callback(call):
        """Обработка нажатий на кнопки постов"""
        post_key = f"{call.message.chat.id}:{call.message.message_id}"

        if post_key not in bot.temp_post_data:
            bot.answer_callback_query(call.id, "❌ Данные поста устарели. Создайте пост заново.")
            return

        post_data = bot.temp_post_data[post_key]
        message_text = post_data['message_text']
        image_url = post_data['image_url']

        if call.data == "post_schedule":
            # Обработка кнопки "Запланировать"
            handle_schedule_post(call, message_text, image_url, post_key)

        elif call.data == "post_now":
            # Обработка кнопки "Опубликовать сейчас"
            handle_publish_now(call, message_text, image_url, post_key)

    def handle_schedule_post(call, message_text, image_url, post_key):
        """Обработка кнопки 'Запланировать'"""
        post_data = bot.temp_post_data[post_key]
        parse_mode = post_data.get('parse_mode', 'HTML')
        schedule_help_text = """
<b>📅 ЗАПЛАНИРОВАТЬ ПОСТ</b>

<u>Формат даты и времени:</u>
<code>ГГГГ-ММ-ДД ЧЧ:ММ</code>

<u>Примеры:</u>
• <code>2024-12-25 18:30</code> - 25 декабря 2024 в 18:30
• <code>2024-12-31 23:59</code> - 31 декабря 2024 в 23:59
• <code>2025-01-01 12:00</code> - 1 января 2025 в 12:00

👇 <b>Введите дату и время в указанном формате:</b>
        """

        bot.edit_message_text(
            schedule_help_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )

        bot.temp_post_data[post_key]['waiting_for_schedule'] = True

        bot.register_next_step_handler_by_chat_id(
            call.message.chat.id,
            process_schedule_time,
            message_text,
            image_url,
            post_key
        )

        bot.answer_callback_query(call.id, "📅 Введите дату и время")

    def process_schedule_time(message, message_text, image_url, post_key, parse_mode):
        """Обработка ввода времени для планирования"""
        try:
            if message.text.startswith('/'):
                bot.reply_to(message, "❌ <b>Планирование отменено.</b>", parse_mode='HTML')
                cleanup_post_data(bot, post_key)
                return

            scheduled_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            now = datetime.now()

            if scheduled_time <= now:
                bot.reply_to(message,
                             "❌ <b>Указанное время уже прошло.</b>\n\n"
                             "Используйте будущую дату и время.",
                             parse_mode='HTML'
                             )
                cleanup_post_data(bot, post_key)
                return

            post_id = db.add_group_post(message.from_user.username, message_text, image_url, scheduled_time.isoformat())

            scheduler.schedule_group_post(post_id, message_text, image_url, scheduled_time,
                                          parse_mode)

            success_text = f"""
    <b>✅ Пост запланирован!</b>

    📝 <b>Превью:</b> {format_post_preview(message_text, 80)}
    📅 <b>Дата публикации:</b> {scheduled_time.strftime('%d.%m.%Y %H:%M')}
    🆔 <b>ID поста:</b> {post_id}
    👤 <b>Автор:</b> @{message.from_user.username or 'Неизвестно'}

    💫 <b>Пост будет автоматически опубликован в группе в указанное время!</b>
            """

            bot.reply_to(message, success_text, parse_mode='HTML')

            cleanup_post_data(bot, post_key)

        except ValueError:
            error_text = """
    ❌ <b>Неверный формат даты/времени!</b>

    <u>Правильный формат:</u>
    <code>ГГГГ-ММ-ДД ЧЧ:ММ</code>

    <u>Примеры правильного ввода:</u>
    • <code>2024-12-25 18:30</code>
    • <code>2024-12-31 23:59</code>
    • <code>2025-01-01 12:00</code>

    👇 <b>Попробуйте еще раз:</b>
            """

            bot.reply_to(message, error_text, parse_mode='HTML')

            bot.register_next_step_handler(
                message,
                process_schedule_time,
                message_text,
                image_url,
                post_key,
                parse_mode
            )
        except Exception as e:
            print(f"Ошибка планирования поста: {e}")
            bot.reply_to(message, "❌ <b>Ошибка при планировании поста.</b>", parse_mode='HTML')
            cleanup_post_data(bot, post_key)

    def handle_publish_now(call, message_text, image_url, post_key):
        """Обработка кнопки 'Опубликовать сейчас'"""

        success = publish_post_now(bot, message_text, image_url)

        if success:

            bot.edit_message_text(
                "✅ <b>Пост успешно опубликован в группе!</b>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )


            preview = format_post_preview(message_text, 100)
            preview_text = f"""
<b>📋 Опубликованный пост:</b>

{preview}

💫 <b>Пост уже опубликован в группе!</b>
            """

            bot.send_message(
                call.message.chat.id,
                preview_text,
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                "❌ <b>Ошибка при публикации поста в группу.</b>\n\n"
                "<b>Проверьте:</b>\n"
                "• Добавлен ли бот в группу\n"
                "• Есть ли у бота права администратора\n"
                "• Может ли бот отправлять сообщения\n\n"
                "💡 <b>Используйте команду</b> <code>/test_post</code> <b>для проверки</b>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )


        cleanup_post_data(bot, post_key)
        bot.answer_callback_query(call.id, "✅ Пост опубликован!" if success else "❌ Ошибка публикации")

    def publish_post_now(bot, message_text, image_url):
        """Мгновенная публикация поста в группу"""
        try:
            if image_url:

                result = bot.send_photo(
                    chat_id=GROUP_CHAT_ID,
                    photo=image_url,
                    caption=message_text,
                    parse_mode='HTML'
                )
                print(f"✅ Фото отправлено в группу. Message ID: {result.message_id}")
            else:

                result = bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=message_text,
                    parse_mode='HTML'
                )
                print(f"✅ Текст отправлен в группу. Message ID: {result.message_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка публикации поста в группу {GROUP_CHAT_ID}: {e}")
            return False

    def cleanup_post_data(bot, post_key):
        """Очистка временных данных поста"""
        if post_key in bot.temp_post_data:
            del bot.temp_post_data[post_key]

    @bot.message_handler(commands=['my_posts'])
    def my_posts_command(message):
        """Мои запланированные посты"""
        user = message.from_user
        posts = db.get_all_group_posts()
        user_posts = [p for p in posts if p[1] == user.username and not p[5]]

        if not user_posts:
            bot.reply_to(message, "📭 <b>У вас нет запланированных постов.</b>", parse_mode='HTML')
            return

        response = "<b>📅 Ваши запланированные посты:</b>\n\n"

        for post in user_posts:
            post_id, author, post_text, image_url, scheduled_time, sent = post
            preview = format_post_preview(post_text, 50)
            time_str = datetime.fromisoformat(scheduled_time).strftime('%d.%m.%Y %H:%M')

            response += f"""
🆔 <b>ID:</b> {post_id}
📝 <b>Текст:</b> {preview}
📅 <b>Время:</b> {time_str}
────────────────────
            """

        bot.reply_to(message, response, parse_mode='HTML')

    @bot.message_handler(commands=['test_post'])
    def test_post_command(message):
        """Тестовая команда для проверки публикации"""
        test_text = """
🧪 <b>Тестовый пост</b>

Это тестовое сообщение для проверки работы бота!

✅ Если вы видите это сообщение в группе, значит бот работает корректно!
🕒 Время отправки: {datetime.now().strftime('%H:%M %d.%m.%Y')}
        """

        success = publish_post_now(bot, test_text, None)

        if success:
            bot.reply_to(message,
                         "✅ <b>Тестовый пост успешно опубликован в группе!</b>\n\n"
                         "💫 Проверьте группу - сообщение должно быть там.",
                         parse_mode='HTML'
                         )
        else:
            bot.reply_to(message,
                         "❌ <b>Ошибка публикации тестового поста.</b>\n\n"
                         "<b>Возможные причины:</b>\n"
                         "• Бот не добавлен в группу\n"
                         "• Бот не является администратором\n"
                         "• Нет прав на отправку сообщений\n"
                         "• Неправильный ID группы\n\n"
                         "🔧 <b>Проверьте настройки бота в группе.</b>",
                         parse_mode='HTML'
                         )

    @bot.message_handler(commands=['post_help'])
    def post_help_command(message):
        """Помощь по созданию постов"""
        show_post_examples(message)