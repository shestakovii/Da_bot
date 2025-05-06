from datetime import datetime
import sqlite3
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

def filter_events_by_time(events):
    """
    Фильтрует события, оставляя только будущие.
    :param events: Список событий (каждое событие — словарь с ключами "event_date" и "event_time").
    :return: Список будущих событий.
    """
    current_time = datetime.now()  # Текущее время запроса
    filtered_events = []

    for event in events:
        event_date = event.get("event_date")
        event_time = event.get("event_time")
        if not event_date or not event_time:
            continue  # Пропускаем события без даты или времени

        try:
            event_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
            if event_datetime > current_time:
                filtered_events.append(event)
        except ValueError:
            logger.error(f"Ошибка при обработке даты/времени события: {event}")

    return filtered_events



def filter_by_category(events, category):
    """
    Фильтрует события по категории.
    :param events: Список событий (каждое событие — словарь с ключом "category").
    :param category: Категория для фильтрации.
    :return: Список событий, соответствующих указанной категории.
    """
    return [
        event for event in events
        if event.get("category") == category
    ]


def filter_by_tags(events, tags):
    """
    Фильтрует события по тегам.
    :param events: Список событий (каждое событие — словарь с ключом "tags").
    :param tags: Список тегов для фильтрации.
    :return: Список событий, содержащих хотя бы один из указанных тегов.
    """
    return [
        event for event in events
        if isinstance(event.get("tags"), str) and any(tag in event["tags"] for tag in tags)
    ]


def filter_by_price_free(events):
    """
    Фильтрует события, оставляя только бесплатные.
    :param events: Список событий (каждое событие — словарь с ключом "price").
    :return: Список бесплатных событий.
    """
    free_keywords = ["Free", "Any", "N/A"]  # Ключевые слова для бесплатных событий
    filtered_events = []

    for event in events:
        price = event.get("price", "").strip()  # Получаем цену и убираем лишние пробелы
        if any(keyword.lower() in price.lower() for keyword in free_keywords):
            filtered_events.append(event)

    return filtered_events


def filter_by_price_not_free(events):
    """
    Фильтрует события, оставляя только платные.
    :param events: Список событий (каждое событие — словарь с ключом "price").
    :return: Список платных событий.
    """
    free_keywords = ["Free", "Any", "N/A"]  # Ключевые слова для бесплатных событий
    filtered_events = []

    for event in events:
        price = event.get("price", "").strip()  # Получаем цену и убираем лишние пробелы
        if not any(keyword.lower() in price.lower() for keyword in free_keywords):
            filtered_events.append(event)

    return filtered_events





def filter_by_likes(events, min_likes):
    """
    Фильтрует события по количеству лайков.
    :param events: Список событий (каждое событие — словарь с ключом "Likes").
    :param min_likes: Минимальное количество лайков.
    :return: Список событий с количеством лайков >= min_likes.
    """
    return [event for event in events if event["Likes"] >= min_likes]