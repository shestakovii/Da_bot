from telebot import types
import html
from datetime import datetime
import logging
from db.operations.db_events import db_increment_event_show_count
from shared.shared_data import user_data
from handlers.errors_handler import handle_network_errors

logger = logging.getLogger(__name__)


def show_events(bot, chat_id: int, user_id: int, events: list, is_next=False, chunk_size = 5):
    if not isinstance(events, list):
        raise TypeError(f"Аргумент events должен быть list, получено: {type(events)}")

    if not events:
        bot.send_message(chat_id, "События не найдены ☹️. Попробуйте изменить фильтры 🧐")
        markup = types.InlineKeyboardMarkup()
        btn_filters = types.InlineKeyboardButton("Изменить фильтры 🔍", callback_data='filters')
        markup.row(btn_filters)
        return []
    

    # Получаем текущий индекс и общее количество событий
    current_index = user_data.get(user_id, {}).get('current_index', 0)
    total_events_count = user_data.get(user_id, {}).get('total_events_count', len(events))
    filtered_events = user_data.get(user_id, {}).get('filtered_events', [])
    message_ids = user_data.get(user_id, {}).get('message_ids', [])
    
    
        # Сохраняем полный список только при первом вызове (не при next_events)
    if not is_next:
        user_data.setdefault(user_id, {})['filtered_events'] = events
        user_data.setdefault(user_id, {})['current_index'] = 0
        user_data.setdefault(user_id, {})['total_events_count'] = len(events)
    
    logger.info(
        f'Вызов show_events. Текущий индекс: {user_data.get(user_id, {}).get("current_index", 0)}, '
        f'Всего событий: {user_data.get(user_id, {}).get("total_events_count", 0)}, '
        f'Фильтрованные события: {len(user_data.get(user_id, {}).get("filtered_events", []))}'
    )
        
     # Берем только текущий чанк событий
    events_to_show = filtered_events[current_index : current_index + chunk_size]
           
    # Формируем текст заглавного сообщения show_events
    show_event_message_text = (
        f"Пожалуйста, отмечайте СОБЫТИЯ, которые вам ИНТЕРЕСНО посетить или НЕ ОЧЕНЬ.\n"
        f"🤖 Я буду стараться учесть ваши предпочтения в будущем.\n"
        f"ПОКАЗАНО СОБЫТИЙ: {min(current_index + 5, total_events_count)} из {total_events_count}"
    )

    # Если есть ID сообщения с прогрессом, редактируем его
    show_events_message_id = user_data.get(user_id, {}).get('show_events_message_id')
    if show_events_message_id:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=show_events_message_id,
            text=show_event_message_text,
            parse_mode="Markdown"
        )
    else:
        # Если ID нет, отправляем новое сообщение и сохраняем его ID
        show_event_message = bot.send_message(chat_id, show_event_message_text, parse_mode="Markdown")
        user_data.setdefault(user_id, {})['show_events_message_id'] = show_event_message.message_id


    message_ids = []  # Список для хранения ID сообщений подборки
    logger.info(f' Список message_ids в НАЧАЛЕ show_ebents: {message_ids}')
    
    for event in events_to_show:
        try:
            formatted_date = datetime.strptime(event['event_date'], "%Y-%m-%d").strftime("%d-%m")
        except (ValueError, TypeError, KeyError):
            formatted_date = "Дата неизвестна"  # Заглушка при ошибке

        message = (
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {event['event_time']}\n"
            f"📍 Место: [{event['event_location_name']}]({event.get('event_location_url', '#')})\n"
            f"🎸 Название: [{event['event_name']}]({event.get('event_name_url', '#')})\n"
            f"🎶 Теги: {', '.join(event['tags']) if event['tags'] else 'Теги не выбраны'}\n"
            f"💵 Стоимость: {event['price']}\n"
        )

        # Создаем inline-клавиатуру с кнопками Like/Dislike
        markup = types.InlineKeyboardMarkup()
        like_btn = types.InlineKeyboardButton("❤️ Like", callback_data=f"like_{event['Id']}")
        dislike_btn = types.InlineKeyboardButton("👎 Dislike", callback_data=f"dislike_{event['Id']}")
        markup.row(like_btn, dislike_btn)

        # Отправляем сообщение и сохраняем его ID
        sent_message = bot.send_message(chat_id, message, reply_markup=markup, disable_web_page_preview=True, parse_mode="Markdown")
        message_ids.append(sent_message.message_id)

        try:
            db_increment_event_show_count(user_id, event['Id'])  # Увеличиваем счетчик показов
        except Exception as e:
            logger.error(f"Ошибка при увеличении счетчика показов: {e}")

    # Добавляем кнопки "Следующие события" и "Изменить фильтры" (ВСЕГДА!)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Следующие события ➡️", callback_data='next_events')
    btn2 = types.InlineKeyboardButton("Изменить фильтры 🔍", callback_data='filters')
    markup.row(btn1)
    markup.row(btn2)
    sent_message = bot.send_message(chat_id, "Хотите увидеть больше событий?", reply_markup=markup, parse_mode="Markdown")
    message_ids.append(sent_message.message_id)  # Сохраняем ID сообщения с кнопкой


    # Обновляем индекс для следующей пагинации
    user_data[user_id]['current_index'] = current_index + len(events_to_show)
    user_data[user_id]['message_ids'] = message_ids
    logger.info(f' Список message_ids в КОНЦЕ show_ebents: {message_ids}')
    return message_ids  # Возвращаем список ID сообщений подборки



def show_next_events_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'next_events')
    @handle_network_errors
    def next_events_handler(callback):
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id

        # Удаляем предыдущие сообщения ПЕРЕД отправкой новых
        if user_id in user_data and 'message_ids' in user_data[user_id]:
            old_message_ids = user_data[user_id]['message_ids'].copy()  # Сохраняем копию
            for message_id in old_message_ids:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception as e:
                    if "message to delete not found" not in str(e):  # Игнорируем уже удаленные
                        logger.error(f"Ошибка при удалении сообщения: {e}")

        # Получаем сохраненные данные пользователя
        filtered_events = user_data.get(user_id, {}).get('filtered_events', [])
        current_index = user_data.get(user_id, {}).get('current_index', 0)
        # total_events_count = user_data.get(user_id, {}).get('total_events_count', 0)

        logger.info(f"Количество событий в user_data.filtered_events: {len(filtered_events)}")

        if filtered_events:
            # Обновляем индекс перед выборкой следующих событий
            next_index = current_index + 5
            next_events = filtered_events[current_index:next_index]

            if next_events:
                # Отправляем следующие события через show_events 
                message_ids = show_events(bot, chat_id, user_id, next_events, is_next=True)
                user_data[user_id]['message_ids'] = message_ids  # Сохраняем ID новых сообщений
                user_data[user_id]['current_index'] = next_index
                bot.answer_callback_query(callback.id, "Загружаем следующие события...")
            else:
                bot.send_message(chat_id, "Вы просмотрели все доступные события.")
                markup = types.InlineKeyboardMarkup()
                btn2 = types.InlineKeyboardButton("Изменить фильтры 🔍", callback_data='filters')
                markup.row(btn2)
                bot.send_message(chat_id, "Хотите изменить фильтры?", reply_markup=markup)
                    
        else:
            bot.answer_callback_query(callback.id, "Мероприятий больше нет.")



