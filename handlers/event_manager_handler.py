import telebot
from handlers.errors_handler import handle_network_errors
from telebot import types
from datetime import datetime
from config import DEFAULT_ROLE
from db.operations import db_update_users
from crew import crew
from crew.agents import parser_agent
from crew.tasks import parse_task
from crew.crew import crew


def setup_event_manager_handler(bot):
    @bot.callback_query_handler(func=lambda callback: callback.data == 'event_manager')
    @handle_network_errors
    def event_manager(callback):
        # Создаем команду для парсинга
        crew = crew(
            agents=[parser_agent],
            tasks=[parse_task]
        )

        # Запускаем команду
        result = crew.kickoff()

        # Отправляем результат пользователю
        bot.send_message(callback.message.chat.id, result)

