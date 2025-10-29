import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from config import GROUP_CHAT_ID

logger = logging.getLogger(__name__)


class SchedulerManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def send_to_group(self, message_text, image_url=None, parse_mode=None):
        """Отправка сообщения в группу"""
        try:
            if image_url:
                result = self.bot.send_photo(
                    chat_id=GROUP_CHAT_ID,
                    photo=image_url,
                    caption=message_text,
                    parse_mode=parse_mode
                )
            else:
                result = self.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=message_text,
                    parse_mode=parse_mode
                )
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            return False

    def send_broadcast(self, message_text, image_url=None, parse_mode="HTML"):
        """Отправка рассылки подписчикам"""
        subscribers = self.db.get_all_subscribers()
        success_count = 0
        fail_count = 0

        logger.info(f"📧 Начинаю рассылку для {len(subscribers)} подписчиков")

        for user_id in subscribers:
            try:
                if image_url:
                    self.bot.send_photo(
                        chat_id=user_id,
                        photo=image_url,
                        caption=message_text,
                        parse_mode=parse_mode
                    )
                else:
                    self.bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode=parse_mode
                    )
                success_count += 1

            except Exception as e:
                logger.error(f"❌ Ошибка отправки пользователю {user_id}: {e}")
                fail_count += 1


                if "bot was blocked" in str(e).lower():
                    self.remove_subscriber(user_id)

        logger.info(f"📊 Рассылка завершена: {success_count} успешно, {fail_count} неудачно")
        return success_count, fail_count

    def remove_subscriber(self, user_id):
        """Удаление подписчика"""
        conn = self.db.conn
        cursor = conn.cursor()
        cursor.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
        conn.commit()
        logger.info(f"🗑️ Удален подписчик: {user_id}")

    def schedule_group_post(self, post_id, message_text, image_url, scheduled_time, parse_mode="HTML"):
        """Планирование поста в группу"""

        def send_scheduled():
            logger.info(f"📨 Отправка запланированного поста в группу ID: {post_id}")
            success = self.send_to_group(message_text, image_url, parse_mode)
            if success:
                self.db.mark_group_post_as_sent(post_id)
                logger.info(f"✅ Пост {post_id} успешно отправлен в группу")
            else:
                logger.error(f"❌ Ошибка отправки поста {post_id} в группу")

        self.scheduler.add_job(
            send_scheduled,
            trigger=DateTrigger(run_date=scheduled_time),
            id=f'group_post_{post_id}'
        )

    def schedule_mailing_post(self, post_id, message_text, image_url, scheduled_time, parse_mode="HTML"):
        """Планирование рассылки"""

        def send_scheduled():
            logger.info(f"📨 Отправка запланированной рассылки ID: {post_id}")
            success_count, fail_count = self.send_broadcast(message_text, image_url,
                                                            parse_mode)
            self.db.mark_mailing_post_as_sent(post_id)
            logger.info(f"✅ Рассылка {post_id} отправлена: {success_count} успешно")

        self.scheduler.add_job(
            send_scheduled,
            trigger=DateTrigger(run_date=scheduled_time),
            id=f'mailing_{post_id}'
        )

    def restore_scheduled_posts(self):
        """Восстановление отложенных постов при запуске"""
        now = datetime.now()


        group_posts = self.db.get_pending_group_posts()
        for post_id, author, message_text, image_url, scheduled_time in group_posts:
            scheduled_dt = datetime.fromisoformat(scheduled_time)
            if scheduled_dt > now:
                self.schedule_group_post(post_id, message_text, image_url, scheduled_dt)
                logger.info(f"🔄 Восстановлен пост в группу ID: {post_id} на {scheduled_dt}")
            else:

                success = self.send_to_group(message_text, image_url)
                if success:
                    self.db.mark_group_post_as_sent(post_id)
                    logger.info(f"🚀 Просроченный пост {post_id} отправлен в группу")


        mailing_posts = self.db.get_pending_mailing_posts()
        for post_id, author, message_text, image_url, scheduled_time in mailing_posts:
            scheduled_dt = datetime.fromisoformat(scheduled_time)
            if scheduled_dt > now:
                self.schedule_mailing_post(post_id, message_text, image_url, scheduled_dt)
                logger.info(f"🔄 Восстановлена рассылка ID: {post_id} на {scheduled_dt}")
            else:
                success_count, fail_count = self.send_broadcast(message_text, image_url)
                self.db.mark_mailing_post_as_sent(post_id)
                logger.info(f"🚀 Просроченная рассылка {post_id} отправлена")

    def shutdown(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()