from crewai import Task
from .agents import parser_agent 

# Задача для парсера
parse_task = Task(
    description="Your task is to parse events for user. Be careful for the information. Don't miss a thing. Be sure to write all info in the database",
    agent=parser_agent,
    expected_output="Список мероприятий с сайта rockgig.net."
)

# # Задача для классификатора
# classify_task = Task(
#     description="Сортировка мероприятий по категориям.",
#     agent=classifier_agent,
# )

# # Задача для фильтра по стоимости
# filter_task = Task(
#     description="Фильтрация мероприятий по стоимости.",
#     agent=price_filter_agent,
# )

# # Задача для рекомендательной системы
# recommend_task = Task(
#     description="Составление персонализированных подборок.",
#     agent=recommender_agent,
# )

# # Задача для интегратора
# integrate_task = Task(
#     description="Формирование финального ответа для пользователя.",
#     agent=integrator_agent,
# )