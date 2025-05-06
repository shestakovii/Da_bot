from functools import wraps
from datetime import datetime
import requests
import logging
from filters.event_filters import filter_by_category, filter_by_tags, filter_by_price_free, filter_by_price_not_free, filter_events_by_time
from db.operations.db_events import db_get_events
logger = logging.getLogger(__name__)



def apply_filters(events, filters):
    """
    Применяет фильтры к списку событий.
    :param events: Список событий из БД.
    :param filters: Словарь с выбранными фильтрами (city, tags, price и т.д.).
    :return: Отфильтрованный список событий.
    """
    # Проверяем, что events — это список
    if not isinstance(events, list):
        logger.error("Ошибка: events не является списком.")
        return []
    
    # Проверяем, что filters — это словарь
    if not isinstance(filters, dict):
        logger.error("Ошибка: filters не является словарем.")
        return []
    
    # Инициализируем отфильтрованные события
    logger.info(f'ФФФФФфильтры при инициализации: {filtered_events}')
    # Фильтр по городу
    if filters.get("city"):
        filtered_events = [
            event for event in filtered_events
            if isinstance(event.get("event_city"), str) and event["event_city"] == filters["city"]
        ]

    # Фильтр по категории
    if filters.get("category"):
        filtered_events = [
            event for event in filtered_events
            if isinstance(event.get("category"), str) and event["category"] == filters["category"]
        ]

    # Фильтр по тегам
    if filters.get("tags"):
        tag_keywords = {
            "rock": ["rock", "metal", "core", "alternative", "psychedelic", "hard-n-heavy", "punk", "industrial", "noise", "new wave", "brutal death", "screamo", "shoegaze", "ritual industrial", "drone", "grunge", "nu-metal"],
            "jazz": ["jazz", "blues", "ethno jazz", "fusion", "soul", "джаз", "блюз", "funk"],
            "other": ["acoustic", "reggae", "crossover", "неоклассика", "киномузыка", "world", "фламенко", "bard", "романс", "folk", "танго", "юмор", "afro", "improv", "гитара", "ska"],
            "culture": ["опера", "спектакль", "поэзия", "мюзикл", "кабаре", "чтения", "авторская песня", "танец", "балет"],
            "covers": ["covers", "кавера"],
            "electro": ["electro", "minimal", "experimental", "aggrotech", "edm"]
        }

        selected_tags = filters["tags"]
           # Если выбран тег "all", пропускаем фильтрацию по тегам
        if "all" in selected_tags:
            pass
        else:
            prepared_tags = []
            for tag in selected_tags:
                prepared_tags.extend(tag_keywords.get(tag, []))

        filtered_events = [
            event for event in filtered_events
            if any(
                keyword.lower() in tag.lower()  # Сравниваем каждый тег события с ключевым словом
                for tag in (event.get("tags", "") if isinstance(tag, str) else [])
                for keyword in prepared_tags
            )
        ]
        
    logger.info (f'фильтры при обработке ТЕГОВ:{filtered_events}')
    
    # Фильтр по цене
    if filters.get("price") == "free":
        filtered_events = filter_by_price_free(filtered_events)
    elif filters.get("price") == "paid":
        filtered_events = filter_by_price_not_free(filtered_events)

    # Фильтр по времени (оставляем только будущие события)
    filtered_events = filter_events_by_time(filtered_events)
    logger.info (f'фильтры после всех обработок:{filtered_events}')
    # print (filtered_events)
    return filtered_events


# def apply_filters(events, filters):
#     """
#     Применяет фильтры к списку событий.
#     :param events: Список событий из БД.
#     :param filters: Словарь с выбранными фильтрами (city, tags, price и т.д.).
#     :return: Отфильтрованный список событий.
#     """
#     # Проверяем, что events — это список
#     if not isinstance(events, list):
#         logger.error("Ошибка: events не является списком.")
#         return []

#     # Инициализируем отфильтрованные события
#     filtered_events = events
    
#     # Подготовка массива фильтров
#     prepared_filters = {}
    
#     # Фильтр по городу
#     if filters.get("city"):
#         prepared_filters = [
#             event for event in prepared_filters
#             if isinstance(event.get("event_city"), str) and event["event_city"] == filters["city"]
#         ]

#     # Фильтр по категории
#     if filters.get("category"):
#         prepared_filters = [
#             event for event in prepared_filters
#             if isinstance(event.get("category"), str) and event["category"] == filters["category"]
            
#         ]
#     # Фильтр по тегам
#     if filters.get("tags"):
#         tag_keywords = {
#             "rock": ["rock", "metal", "core", "alternative", "psychedelic", "hard-n-heavy", "punk", "industrial", "noise", "new wave", "brutal death", "screamo", "shoegaze", "ritual industrial", "drone", "grunge", "nu-metal"],
#             "jazz": ["jazz", "blues", "ethno jazz", "fusion", "soul", "джаз", "блюз", "funk"],
#             "other": ["acoustic", "reggae", "crossover", "неоклассика", "киномузыка", "world", "фламенко", "bard", "романс", "folk", "танго", "юмор", "afro", "improv", "гитара", "ska"],
#             "culture": ["опера", "спектакль", "поэзия", "мюзикл", "кабаре", "чтения", "авторская песня", "танец", "балет" ],
#             "covers": ["covers", "кавера"],
#             "electronic": ["electro", "minimal", "experimental", "aggrotech", "edm"]
#         }
#         selected_tags = filters["tags"]
#         prepared_tags = []
#         for tag in selected_tags:
#             prepared_tags.extend(tag_keywords.get(tag, []))
#         prepared_filters["tags"] = prepared_tags
        
#        # Фильтр по цене
#     if filters.get("price"):
#         prepared_filters["price"] = filters["price"]   
        
#     if callable(filter_events_by_time):
#         filtered_events = filter_events_by_time(filtered_events)
#     else:
#         logger.error("Ошибка: filter_events_by_time не является функцией.")  
        
#         # Передаем подготовленные фильтры в db_get_events
#     current_date = datetime.now().strftime("%Y-%m-%d")
#     filtered_events = db_get_events(current_date, prepared_filters)

#     return filtered_events    




    # # Фильтр по тегам
    # if filters.get("tags"):
    #     # Проверяем, что tags в filters — это список
    #     if not isinstance(filters["tags"], list):
    #         logger.warning("Ошибка: filters['tags'] не является списком.")
    #         filters["tags"] = []
        
    #     filtered_events = [
    #         event for event in filtered_events
    #         if isinstance(event.get("tags"), str) and any(
    #             isinstance(tag, str) and tag in event["tags"] for tag in filters["tags"]
    #         )
    #     ]

    # Фильтр по цене
    # if filters.get("price") == "free":
    #     # Проверяем, что filter_by_price_free существует и является функцией
    #     if callable(filter_by_price_free):
    #         filtered_events = filter_by_price_free(filtered_events)
    #     else:
    #         logger.error("Ошибка: filter_by_price_free не является функцией.")

    # elif filters.get("price") == "not_free":
    #     # Проверяем, что filter_by_price_not_free существует и является функцией
    #     if callable(filter_by_price_not_free):
    #         filtered_events = filter_by_price_not_free(filtered_events)
    #     else:
    #         logger.error("Ошибка: filter_by_price_not_free не является функцией.")
            
    # Фильтр по времени (оставляем только будущие события)


# # Фильтр по цене
#     if filters.get("price") == "free":
#         filtered_events = [
#             event for event in filtered_events
#             if event.get("price", "").lower() in ["free", "n/a"]
#         ]
#     elif filters.get("price") == "not_free":
#         filtered_events = [
#             event for event in filtered_events
#             if event.get("price", "").lower() not in ["free", "n/a"]
#         ]

    # # Фильтр по времени
    # filtered_events = [
    #     event for event in filtered_events
    #     if datetime.strptime(f"{event['event_date']} {event['event_time']}", "%Y-%m-%d %H:%M") > datetime.now()
    # ]
    
    #     # Фильтр по времени (оставляем только будущие события)
    # filtered_events = filter_events_by_time(filtered_events)



def apply_city_filter(events, city):
    """
    Фильтрует события по городу.
    :param events: Список событий.
    :param city: Город для фильтрации.
    :return: Отфильтрованный список событий.
    """
    return [event for event in events if event["EventCity"] == city]

def apply_category_filter(events, category):
    """
    Фильтрует события по категории.
    :param events: Список событий.
    :param category: Категория для фильтрации.
    :return: Отфильтрованный список событий.
    """
    return [event for event in events if event["Category"] == category]

def apply_tags_filter(events, tags):
    """
    Фильтрует события по тегам.
    :param events: Список событий.
    :param tags: Список тегов для фильтрации.
    :return: Отфильтрованный список событий.
    """
    return [event for event in events if any(tag in event["Tags"] for tag in tags)]

def apply_price_filter(events, price):
    """
    Фильтрует события по цене.
    :param events: Список событий.
    :param price: Условие фильтрации ("free", "1000" и т.д.).
    :return: Отфильтрованный список событий.
    """
    if price == "free":
        return [event for event in events if event["Price"] in ["Free", "Any", "N/A"]]
    elif price == "1000":
        return [event for event in events if event["Price"] <= 1000]
    return events

def apply_likes_filter(events, min_likes):
    """
    Фильтрует события по количеству лайков.
    :param events: Список событий.
    :param min_likes: Минимальное количество лайков.
    :return: Отфильтрованный список событий.
    """
    return [event for event in events if event["Likes"] >= min_likes]