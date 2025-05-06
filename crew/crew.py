import sys
import os
from typing import Type  # Добавляем импорт Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from crewai import Crew
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .agents import parser_agent
from .tasks import parse_task
# from crew.agents import parser_agent, classifier_agent, price_filter_agent, recommender_agent, integrator_agent
# from crew.tasks import parse_task, classify_task, filter_task, recommend_task, integrate_task

# Создание команды
crew = Crew(
    agents=[parser_agent],
    tasks=[parse_task],
)

# Запуск команды
result = crew.kickoff()
print(result)