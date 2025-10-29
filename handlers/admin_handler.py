from datetime import datetime
from utils.helpers import is_admin, format_post_preview


def setup_admin_handlers(bot, db, scheduler):
    """Настройка админских обработчиков"""

    @bot.message_handler(commands=['scheduled'])
    def scheduled_command(message):
        """Список всех запланированных постов"""
        user = message.from_user

        if not is_admin(user.username):
            bot.reply_to(message, "❌ <b>У вас нет прав для этой команды.</b>", parse_mode='HTML')
            return

        group_posts = db.get_all_group_posts()
        mailing_posts = db.get_all_mailing_posts()

        all_posts = [(p, 'group') for p in group_posts if not p[5]] + [(p, 'mailing') for p in mailing_posts if
                                                                       not p[5]]

        if not all_posts:
            bot.reply_to(message, "📭 <b>Нет запланированных постов.</b>", parse_mode='HTML')
            return

        response = "<b>📅 Все запланированные посты:</b>\n\n"

        for post_data in all_posts:
            post, post_type = post_data
            post_id, author, post_text, image_url, scheduled_time, sent = post

            type_emoji = "📝" if post_type == 'group' else "📧"
            type_text = "Пост в группу" if post_type == 'group' else "Рассылка"

            preview = format_post_preview(post_text, 40)
            time_str = datetime.fromisoformat(scheduled_time).strftime('%d.%m.%Y %H:%M')

            response += f"""
{type_emoji} <b>{type_text}</b>
🆔 <b>ID:</b> {post_id}
👤 <b>Автор:</b> @{author}
📝 <b>Текст:</b> {preview}
📅 <b>Время:</b> {time_str}
────────────────────
            """

        bot.reply_to(message, response, parse_mode='HTML')

    @bot.message_handler(commands=['cancel'])
    def cancel_command(message):
        """Отмена запланированного поста"""
        user = message.from_user

        if not is_admin(user.username):
            bot.reply_to(message, "❌ <b>У вас нет прав для этой команды.</b>", parse_mode='HTML')
            return

        args = message.text.split()[1:]

        if not args:
            bot.reply_to(message, "❌ <b>Укажите ID поста: /cancel ID_поста</b>", parse_mode='HTML')
            return

        try:
            post_id = int(args[0])

            db.delete_group_post(post_id)
            db.delete_mailing_post(post_id)

            try:
                scheduler.scheduler.remove_job(f'group_post_{post_id}')
            except:
                pass

            try:
                scheduler.scheduler.remove_job(f'mailing_{post_id}')
            except:
                pass

            bot.reply_to(message, f"✅ <b>Пост ID:{post_id} отменен и удален.</b>", parse_mode='HTML')

        except ValueError:
            bot.reply_to(message, "❌ <b>Неверный ID поста.</b>", parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, "❌ <b>Ошибка при отмене поста.</b>", parse_mode='HTML')

    @bot.message_handler(commands=['stats'])
    def stats_command(message):
        """Статистика бота"""
        user = message.from_user

        if not is_admin(user.username):
            bot.reply_to(message, "❌ <b>У вас нет прав для этой команды.</b>", parse_mode='HTML')
            return

        subscribers = db.get_all_subscribers()
        group_posts = db.get_all_group_posts()
        mailing_posts = db.get_all_mailing_posts()

        sent_group = len([p for p in group_posts if p[5]])
        pending_group = len([p for p in group_posts if not p[5]])
        sent_mailing = len([p for p in mailing_posts if p[5]])
        pending_mailing = len([p for p in mailing_posts if not p[5]])

        stats_text = f"""
<b>📊 Статистика бота:</b>

👥 <b>Подписчиков:</b> {len(subscribers)}

<b>📝 Посты в группу:</b>
• Всего: {len(group_posts)}
• Отправлено: {sent_group}
• Ожидает: {pending_group}

<b>📧 Рассылки:</b>
• Всего: {len(mailing_posts)}
• Отправлено: {sent_mailing}
• Ожидает: {pending_mailing}
        """

        bot.reply_to(message, stats_text, parse_mode='HTML')