import telebot
from telebot import types
import logging
from datetime import datetime
from config import DEFAULT_CITY
from config import BOT_TOKEN
# from services.filter_service import apply_filters
from handlers.show_events_handler import show_events
from db.operations.db_events import db_get_events
from db.operations.db_users import db_get_user_city, db_update_user_city
from filters.event_filters import filter_by_price_free, filter_by_price_not_free, filter_events_by_time
from shared.shared_data import user_data
from datetime import datetime, timedelta
from handlers.errors_handler import handle_network_errors

bot = telebot.TeleBot(BOT_TOKEN)
logger = logging.getLogger(__name__)
user_filters = {}
user_filtered_events = {}
apply_filters_handler_func = None

def setup_filter_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'filters')
    @handle_network_errors
    def handle_filters_callback(callback):
        try:
            user_id = callback.from_user.id
            chat_id = callback.message.chat.id
            
            # 1. Проверка города
            city = db_get_user_city(user_id)
            if not city:
                city = DEFAULT_CITY
                db_update_user_city(user_id, city)
                logger.info(f"Установлен город по умолчанию: {city} для user_id={user_id}")
            
            # 2. Запуск процесса фильтрации
            show_category_selection(bot, chat_id, user_id, city)
            
        except Exception as e:
            logger.error(f"Ошибка в handle_filters_callback: {e}")
            bot.answer_callback_query(callback.id, "Ошибка при обработке фильтров")

def show_category_selection(bot, chat_id, user_id, city):
    """Шаг 1: Выбор категории мероприятия"""
    try:
        # Инициализация фильтров для пользователя
        if user_id not in user_filters:
            user_filters[user_id] = {
                "category": None,
                "tags": [],
                "price": None,
                "city": city
            }
            
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🎤 Концерты", callback_data='filter_category_concert'),
            types.InlineKeyboardButton("🎭 Афиша МО", url = f'https://visitmo.ru/events/')
        )
        bot.send_message(chat_id, "Выберите категорию мероприятия:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка в show_category_selection: {e}")

def show_tags_selection(bot, chat_id, user_id, message_id):
    """Шаг 2: Выбор тегов (множественный выбор)"""
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Текущие выбранные теги пользователя
        current_tags = user_filters.get(user_id, {}).get("tags", [])
        
        buttons = [
            types.InlineKeyboardButton(
                f"🎸 Рок {'✅' if 'rock' in current_tags else ''}",
                callback_data='filter_tag_rock'
            ),
            types.InlineKeyboardButton(
                f"🎷 Jazz/Blues {'✅' if 'jazz' in current_tags else ''}",
                callback_data='filter_tag_jazz'
            ),
            types.InlineKeyboardButton(
                f"🛸 Электро {'✅' if 'electro' in current_tags else ''}",
                callback_data='filter_tag_electro'
            ),
            types.InlineKeyboardButton(
                f"🎭 Культура {'✅' if 'culture' in current_tags else ''}",
                callback_data='filter_tag_culture'
            ),
            types.InlineKeyboardButton(
                f"🎤 Каверы {'✅' if 'covers' in current_tags else ''}",
                callback_data='filter_tag_covers'
            ),
            types.InlineKeyboardButton(
                f"♫ Другое {'✅' if 'other' in current_tags else ''}",
                callback_data='filter_tag_other'
            )
        ]
        
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("👀 Показать всё", callback_data='filter_select_all_tags'))
        markup.add(types.InlineKeyboardButton("Далее →", callback_data='next_to_price'))
        
        bot.edit_message_text(
            "Выберите теги мероприятий (можно несколько):",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Ошибка в show_tags_selection: {e}")


def show_price_selection(bot, chat_id, user_id, message_id):
    """Шаг 3: Выбор цены"""
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        current_price = user_filters.get(user_id, {}).get("price")
        
        buttons = [
            types.InlineKeyboardButton(
                f"🆓 Бесплатно {'' if current_price == 'free' else ''}",
                callback_data='apply_price_free'
            ),
            types.InlineKeyboardButton(
                f"💲 Платные {'' if current_price == 'paid' else ''}",
                callback_data='apply_price_paid'
            ),
            types.InlineKeyboardButton(
                f"👀 Показать всё {'' if current_price is None else ''}",
                callback_data='apply_price_all'
            )
        ]
        
        # Распределяем кнопки: первые две в одну строку, третью отдельно
        markup.add(buttons[0], buttons[1])
        markup.add(buttons[2])
        
        bot.edit_message_text(
            "Выберите ценовой диапазон:",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Ошибка в show_price_selection: {e}")



def setup_filter_category_selection_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('filter_category_'))
    @handle_network_errors
    def handle_category_selection(callback):
        try:
            user_id = callback.from_user.id
            category = callback.data.split('_')[-1]
            
            # Обновляем фильтры
            if user_id not in user_filters:
                user_filters[user_id] = {}
            user_filters[user_id]['category'] = category
            
            # Переходим к выбору тегов
            show_tags_selection(bot, callback.message.chat.id, user_id, callback.message.message_id)
            
        except Exception as e:
            logger.error(f"Ошибка в handle_category_selection: {e}")

def setup_filter_tag_selection_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('filter_tag_'))
    @handle_network_errors
    def handle_tag_selection(callback):
        try:
            user_id = callback.from_user.id
            tag = callback.data.split('_')[-1]
            
            if tag in user_filters.get(user_id, {}).get('tags', []):
                user_filters[user_id]['tags'].remove(tag)
            else:
                if 'tags' not in user_filters[user_id]:
                    user_filters[user_id]['tags'] = []
                user_filters[user_id]['tags'].append(tag)
                    
            logger.info(f"Текущие фильтры на этапе выбора ТЕГОВ для user_id={user_id}: {user_filters[user_id]}")
            # Обновляем клавиатуру
            show_tags_selection(bot, callback.message.chat.id, user_id, callback.message.message_id)
            
        except Exception as e:
            logger.error(f"Ошибка в handle_tag_selection: {e}")

def setup_filter_all_tags_selection_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'filter_select_all_tags')
    @handle_network_errors
    def handle_all_tags_selection(callback):
        """Обработчик кнопки 'Показать всё'"""
        try:
            user_id = callback.from_user.id
            chat_id = callback.message.chat.id
            
            # 1. Сбрасываем выбранные теги
            user_filters[user_id]['tags'] = []
            
            # 2. Даем обратную связь пользователю
            bot.answer_callback_query(callback.id, "Выбраны все теги")
            
            # 3. Сразу переходим к выбору цены (вместо повторного показа тегов)
            show_price_selection(bot, chat_id, user_id, callback.message.message_id)
            
        except Exception as e:
            logger.error(f"Ошибка в handle_show_all: {e}")
            bot.answer_callback_query(callback.id, "Ошибка")



def setup_filter_next_to_price_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'next_to_price')
    @handle_network_errors
    def handle_next_to_price(callback):
        try:
            user_id = callback.from_user.id
            show_price_selection(bot, callback.message.chat.id, user_id, callback.message.message_id)
        except Exception as e:
            logger.error(f"Ошибка в handle_next_to_price: {e}")
            

def setup_filter_price_selection_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data.startswith('apply_price_'))
    @handle_network_errors
    def handle_price_selection(callback):
        try:
            user_id = callback.from_user.id
            chat_id = callback.message.chat.id
            price_filter = callback.data.split('_')[-1]
            # Устанавливаем фильтр
            if price_filter == 'all':
                user_filters[user_id]['price'] = None
            else:
                user_filters[user_id]['price'] = price_filter
            logger.info(f"Текущие фильтры при выборе ЦЕНЫ для user_id={user_id}: {user_filters[user_id]}")
            # Создаем искусственное событие apply_filters
            class FakeCallback:
                def __init__(self, original):
                    self.data = 'apply_filters'
                    self.from_user = original.from_user
                    self.message = original.message
                    self.id = original.id
            # Вызываем обработчик apply_filters через глобальную переменную
            global apply_filters_handler_func
            apply_filters_handler_func(FakeCallback(callback))
            
            # Удаляем сообщение с выбором цены
            try:
                bot.delete_message(chat_id, callback.message.message_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")
        except Exception as e:
            logger.error(f"Ошибка в handle_price_selection: {e}")
            bot.answer_callback_query(callback.id, "Ошибка при применении фильтров")

            

def setup_filter_apply_filters_handler(bot):
    global apply_filters_handler_func
    @bot.callback_query_handler(func=lambda callback: callback.data == 'apply_filters')
    @handle_network_errors
    def apply_filters_handler(callback):
        try:
            user_id = callback.from_user.id
            chat_id = callback.message.chat.id
            
            # Добавляем фильтр по городу
            city = db_get_user_city(user_id)
            if city:
                if user_id not in user_filters:
                    user_filters[user_id] = {}
                user_filters[user_id]['city'] = city
            
            current_datetime = datetime.now()
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f'User_filters перед запросом в БД: {user_filters.get(user_id, {})}')
            
            # 1. Сначала получаем события из БД (только по базовым фильтрам: город, дата)
            events = db_get_events(current_date, {'city': user_filters.get(user_id, {}).get('city')})
            if not isinstance(events, list):
                logger.error("Ошибка: db_get_events вернул некорректные данные.")
                bot.answer_callback_query(callback.id, "Произошла ошибка при загрузке событий.")
                return
            
            # 2. Затем применяем фильтры
            filtered_events = events
            user_filter_data = user_filters.get(user_id, {})
            logger.info(f'События {len(filtered_events)} при первом получении событий из БД (ШАГ 2)')  
            
            # Фильтр по категории
            if user_filter_data.get("category"):
                filtered_events = [
                    event for event in filtered_events
                    if isinstance(event.get("category"), str) and 
                    event["category"].lower() == user_filter_data["category"].lower()
                ]
                logger.info(f'События {len(filtered_events)} после фильтрации по категории')
            
            # Фильтр по тегам
            # if user_filter_data.get("tags"):
            if len(user_filter_data["tags"]) > 0:
                tag_keywords = {
                    "rock": ["rock", "metal", "core", "alternative", "psychedelic", "hard-n-heavy", 
                            "punk", "industrial", "noise", "new wave", "brutal death", "screamo", 
                            "shoegaze", "ritual industrial", "drone", "grunge", "nu-metal"],
                    "jazz": ["jazz", "blues", "ethno jazz", "fusion", "soul", "джаз", "блюз", "funk"],
                    "other": ["acoustic", "reggae", "crossover", "неоклассика", "киномузыка"],
                    "culture": ["опера", "спектакль", "поэзия", "мюзикл", "кабаре"],
                    "covers": ["covers", "кавера"],
                    "electro": ["electro", "minimal", "experimental", "aggrotech", "edm"]
                }

                prepared_tags = []
                for tag in user_filter_data["tags"]:
                    prepared_tags.extend(tag_keywords.get(tag, []))
                  
                    # Преобразуем теги события в список, если они в строке
                    def get_tags_list(event_tags):
                        if isinstance(event_tags, list):
                            return event_tags
                        elif isinstance(event_tags, str):
                            return [tag.strip() for tag in event_tags.split(",")]
                        return []
                    
                    filtered_events = [
                        event for event in filtered_events
                        if any(
                            any(
                                keyword.lower() in tag.lower()
                                for tag in get_tags_list(event.get("tags", ""))
                            )
                            for keyword in prepared_tags
                        )
                    ]
                logger.info(f'События {len(filtered_events)} после фильтрации по тегам')
            
            # Фильтр по цене
            if user_filter_data.get("price") == "free":
                filtered_events = filter_by_price_free(filtered_events)
                logger.info(f'События {len(filtered_events)} после фильтрации по цене (free)')
            elif user_filter_data.get("price") == "paid":
                filtered_events = filter_by_price_not_free(filtered_events)
                logger.info(f'События {len(filtered_events)} после фильтрации по цене (paid):{filtered_events}')
                
                
            # 2.1. Предварительная проверка формата времени
            valid_events = []
            for event in filtered_events:
                try:
                    datetime.strptime(f"{event['event_date']} {event['event_time']}", "%Y-%m-%d %H:%M")
                    valid_events.append(event)
                except Exception as e:
                    logger.warning(f"Некорректное время в событии {event.get('Id')}: {e}")


            # time_threshold = datetime.now() - timedelta(hours=2)

            # # Фильтрация событий
            # filtered_events = [
            #     event for event in filtered_events
            #     if event.get('event_date') and event.get('event_time')
            #     and datetime.strptime(f"{event['event_date']} {event['event_time']}", "%Y-%m-%d %H:%M") >= time_threshold
            # ]
            
            logger.info(f'Финальный список {len(filtered_events)} событий после всех фильтров')
            
            total_events_count = len(filtered_events)
            user_data[user_id] = {
                "filtered_events": filtered_events,
                "current_index": 0,
                "total_events_count": total_events_count,
                "show_events_message_id": None # ID сообщения с прогрессом для show_events
            }

            # Сохраняем отфильтрованные события в глобальную переменную
            logger.info(f"в Filters_handler Сохранено {len(filtered_events)} событий для user_id={user_id}")
            logger.info(f'Сохранен список user_data: {user_data}')
    
            # Показываем результат           
            show_events(bot, chat_id, user_id, filtered_events)
            
            # Очищаем фильтры
            if user_id in user_filters:
                del user_filters[user_id]
                
        except Exception as e:
            logger.error(f"Ошибка в apply_filters_handler: {e}")
            bot.answer_callback_query(callback.id, "Ошибка при применении фильтров")
            
    apply_filters_handler_func = apply_filters_handler
