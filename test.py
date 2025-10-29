import telebot
from config import BOT_TOKEN, GROUP_CHAT_ID

bot = telebot.TeleBot(BOT_TOKEN)


def test_group_access():
    """Тестирование доступа бота к группе"""
    try:
        print(f"🤖 Тестирую доступ к группе {GROUP_CHAT_ID}...")

        # Пробуем получить информацию о чате
        chat_info = bot.get_chat(GROUP_CHAT_ID)
        print(f"✅ Группа найдена: {chat_info.title}")
        print(f"   Тип: {chat_info.type}")

        # Пробуем отправить тестовое сообщение
        test_msg = bot.send_message(
            GROUP_CHAT_ID,
            "🤖 <b>Тестовое сообщение от бота</b>\n\n"
            "Если вы видите это сообщение, значит бот имеет права на публикацию в группе!",
            parse_mode='HTML'
        )
        print(f"✅ Тестовое сообщение отправлено! ID: {test_msg.message_id}")

        # Пробуем отправить фото
        try:
            photo_msg = bot.send_photo(
                GROUP_CHAT_ID,
                photo="https://i.pinimg.com/736x/d4/38/c3/d438c31d0caf10b0dc17a5fcb503a38e.jpg",
                caption="🖼️ <b>Тестовое изображение</b>\n\nПроверка отправки медиа",
                parse_mode='HTML'
            )
            print(f"✅ Тестовое фото отправлено! ID: {photo_msg.message_id}")
        except Exception as e:
            print(f"⚠️ Фото не отправлено (возможно нет прав): {e}")

        print("\n🎉 Бот успешно прошел тест! Права в порядке.")

    except Exception as e:
        print(f"❌ Ошибка доступа к группе: {e}")
        print("\n🔧 Возможные решения:")
        print("1. Убедитесь, что бот добавлен в группу")
        print("2. Убедитесь, что бот является администратором")
        print("3. Проверьте ID группы")
        print("4. Убедитесь, что у бота есть права на отправку сообщений")


if __name__ == '__main__':
    test_group_access()