from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from handlers.parse_rockgig_handler import parse_rockgig

class ParseRockgigInput(BaseModel):
    """Input schema for ParseRockgigTool."""
    date: str = Field(..., description="Дата для парсинга мероприятий в формате YYYY-MM-DD.")

class ParseRockgigTool(BaseTool):
    name: str = "parse_rockgig"
    description: str = "Парсинг сайта rockgig.net для извлечения данных о мероприятиях."
    args_schema: type[BaseModel] = ParseRockgigInput

    def _run(self, date: str) -> list:
        """Метод для выполнения парсинга."""
        return parse_rockgig(date)