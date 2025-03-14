__all__ = [
    "DepositSchema", "SixSigmaSchema",
    "ApiAgent", "Supervisor"
]

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import starmap
from typing import Any, Literal

import requests
from aiogram.types import Message
from dateutil.relativedelta import relativedelta
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from pydantic import BaseModel, computed_field, Field


@dataclass
class Example:
    """
    Пример для обучения агента-диспетчера выбору целевого агента.
    """

    message: str
    answer : str

    def __str__(self) -> str:
        return f"Сообщение: {self.message}\nОтвет: {self.answer}"


@dataclass(kw_only=True)
class BaseAgent(ABC):
    """
    Базовый класс агентов.
    """

    model : GigaChat
    prompt: str

    @abstractmethod
    def handle_message(self, message: Message):
        """Обработать сообщение пользователя. """
        raise NotImplementedError


@dataclass
class Supervisor(BaseAgent):
    """
    Агент-диспетчер.
    """

    def handle_message(self, message: Message) -> str:
        """Определить имя целевого агента. """
        messages = [SystemMessage(self.prompt), HumanMessage(message.text)]
        return self.model.invoke(messages).content


@dataclass(kw_only=True)
class TargetAgent(BaseAgent):
    """
    Базовый класс целевых агентов.
    """

    mission : str                    # функциональное назначение агента
    examples: list[tuple[str, str]]  # примеры для обучения диспетчера выбору
                                     # целевого агента

    def __post_init__(self) -> None:
        messages = [f"• <i>{msg}</i>" for msg in dict(self.examples)]
        self.mission = "\n".join([
            self.mission, "Примеры запросов:", *messages
        ])
        self.examples = list(starmap(Example, self.examples))

    def __str__(self) -> str:
        return "\n\n".join(map(str, self.examples))


HTTP_METHODS = ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT")


@dataclass(kw_only=True)
class ApiAgent(TargetAgent):
    """
    Агент для интеграции бота с произвольным API.
    """

    schema      : BaseModel
    method      : Literal[HTTP_METHODS]  # type: ignore
    url         : str
    payload_name: str  # имя параметра функции requests.request для передачи
                       # тела запроса или его параметров

    def __post_init__(self) -> None:
        self.mission += f" в\n{self.url}"
        super().__post_init__()

    def extract_data(self, message: Message) -> dict[str, Any]:
        """
        Извлечь из сообщения структурированные данные для отправки в API.
        """
        runnable = (
            self.prompt | self.model.with_structured_output(self.schema)
        )
        return runnable.invoke({"message": message.text}).model_dump()

    def handle_message(self, message: Message) -> requests.Response:
        """Отправить запрос в API и вернуть ответ. """
        payload = {self.payload_name: self.extract_data(message)}
        return requests.request(self.method, self.url, **payload)


class DepositSchema(BaseModel):
    """
    Параметры депозита для запроса к
    https://compound-interest-calculator.containerapps.ru/standard.
    """

    periods: int | None = Field(
        description="продолжительность депозита в месяцах"
    )
    amount:  int | None = Field(
        description="начальная сумма депозита"
    )
    rate:  float | None = Field(
        description="годовая процентная ставка по депозиту"
    )

    @computed_field
    def date(self) -> str:
        """
        Дата первой капитализации процентов на депозит: сегодня + 1 мес.
        """
        first_interest = datetime.date.today() + relativedelta(months=1)
        return first_interest.strftime("%d.%m.%Y")


class SixSigmaSchema(BaseModel):
    """
    Параметры процесса для запроса к https://six-sigma.containerapps.ru/plot.
    """

    tests: int = Field(
        description="общее количество экземпляров, случаев, исходов или тестов"
    )
    fails: int = Field(
        description=(
            "количество экземпляров, случаев, исходов или тестов, "
            "завершившихся неудачей, сбоем или дефектом"
        )
    )
    name: str | None = Field(
        default=None,
        description="имя, метка или кодовое обозначение процесса или изделия"
    )
