import html as html_escape
import re
import logging
from config import ADMIN_USERNAMES

logger = logging.getLogger(__name__)


def is_admin(username):
    """Проверка прав администратора"""
    if not username:
        logger.warning(f"❌ Username is None or empty")
        return False

    user_username = username.lower().strip()
    admin_list = [admin.lower().strip() for admin in ADMIN_USERNAMES]

    logger.info(f"🔍 Проверка прав: '{user_username}' в {admin_list}")

    return user_username in admin_list


def extract_message_data(message):
    """Извлечение данных из сообщения"""
    message_text = ""
    image_url = None
    parse_mode = None

    if message.reply_to_message:
        original = message.reply_to_message
        if original.caption:
            message_text = original.caption
        elif original.text:
            message_text = original.text

        if original.photo:
            image_url = original.photo[-1].file_id
    else:
        message_text = message.text

    message_text = re.sub(r'^/\w+\s*', '', message_text).strip()

    image_match = re.search(r'\[img:(https?://[^\]]+)\]', message_text)
    if image_match:
        image_url = image_match.group(1)
        message_text = re.sub(r'\[img:https?://[^\]]+\]', '', message_text).strip()

    parse_mode = None

    return message_text, image_url, parse_mode


def convert_entities_to_html(text, entities):
    """
    Конвертирует Telegram entities в HTML форматирование
    """
    if not entities:
        return html_escape.escape(text)

    sorted_entities = sorted(entities, key=lambda x: x.offset, reverse=True)

    result = text

    for entity in sorted_entities:
        start = entity.offset
        end = entity.offset + entity.length

        if start >= len(result) or end > len(result):
            continue

        entity_text = result[start:end]

        if entity.type == "bold":
            replacement = f"<b>{html_escape.escape(entity_text)}</b>"
        elif entity.type == "italic":
            replacement = f"<i>{html_escape.escape(entity_text)}</i>"
        elif entity.type == "underline":
            replacement = f"<u>{html_escape.escape(entity_text)}</u>"
        elif entity.type == "strikethrough":
            replacement = f"<s>{html_escape.escape(entity_text)}</s>"
        elif entity.type == "code":
            replacement = f"<code>{html_escape.escape(entity_text)}</code>"
        elif entity.type == "pre":
            replacement = f"<pre>{html_escape.escape(entity_text)}</pre>"
        elif entity.type == "text_link":
            replacement = f'<a href="{entity.url}">{html_escape.escape(entity_text)}</a>'
        elif entity.type == "spoiler":
            replacement = f'<tg-spoiler>{html_escape.escape(entity_text)}</tg-spoiler>'
        else:
            replacement = html_escape.escape(entity_text)

        result = result[:start] + replacement + result[end:]

    return result


def convert_entities_safe(text, entities):
    """
    Безопасная конвертация entities с сохранением ссылок
    """
    safe_text = html_escape.escape(text)

    sorted_entities = sorted(entities, key=lambda x: x.offset, reverse=True)

    result = safe_text

    for entity in sorted_entities:
        start = entity.offset
        end = entity.offset + entity.length

        if start >= len(result) or end > len(result):
            continue

        entity_text = text[start:end]

        if entity.type == "bold":
            replacement = f"<b>{html_escape.escape(entity_text)}</b>"
        elif entity.type == "italic":
            replacement = f"<i>{html_escape.escape(entity_text)}</i>"
        elif entity.type == "underline":
            replacement = f"<u>{html_escape.escape(entity_text)}</u>"
        elif entity.type == "strikethrough":
            replacement = f"<s>{html_escape.escape(entity_text)}</s>"
        elif entity.type == "code":
            replacement = f"<code>{html_escape.escape(entity_text)}</code>"
        elif entity.type == "pre":
            replacement = f"<pre>{html_escape.escape(entity_text)}</pre>"
        elif entity.type == "text_link":
            # Для ссылок используем HTML теги
            replacement = f'<a href="{entity.url}">{html_escape.escape(entity_text)}</a>'
        elif entity.type == "spoiler":
            replacement = f'<tg-spoiler>{html_escape.escape(entity_text)}</tg-spoiler>'
        else:
            replacement = html_escape.escape(entity_text)

        result = result[:start] + replacement + result[end:]

    return result


def convert_entities_to_markdown(text, entities):
    """
    Конвертирует Telegram entities в Markdown форматирование
    """
    if not entities:
        return text

    sorted_entities = sorted(entities, key=lambda x: x.offset, reverse=True)
    result = text

    for entity in sorted_entities:
        start = entity.offset
        end = entity.offset + entity.length

        if start >= len(result) or end > len(result):
            continue

        entity_text = result[start:end]

        if entity.type == "bold":
            replacement = f"**{entity_text}**"
        elif entity.type == "italic":
            replacement = f"_{entity_text}_"
        elif entity.type == "code":
            replacement = f"`{entity_text}`"
        elif entity.type == "pre":
            replacement = f"```{entity_text}```"
        elif entity.type == "text_link":
            replacement = f"[{entity_text}]({entity.url})"
        else:
            if entity.type == "underline":
                replacement = f"<u>{entity_text}</u>"
            elif entity.type == "strikethrough":
                replacement = f"<s>{entity_text}</s>"
            elif entity.type == "spoiler":
                replacement = f"<tg-spoiler>{entity_text}</tg-spoiler>"
            else:
                replacement = entity_text

        result = result[:start] + replacement + result[end:]

    return result


def format_post_preview(text, max_length=100):
    """Форматирование превью поста"""
    if not text:
        return "🖼️ Сообщение с изображением"

    clean_text = re.sub(r'<[^>]+>', '', text)

    if len(clean_text) > max_length:
        return clean_text[:max_length] + "..."

    return clean_text