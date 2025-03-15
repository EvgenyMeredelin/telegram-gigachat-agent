__all__ = [
    "menu", "supervisor",
    "OFFTOP_SENTINEL", "fallback_answer"
]

import inspect
import sys

from decouple import config
from langchain_core.prompts import ChatPromptTemplate
from langchain_gigachat.chat_models import GigaChat

from models import *


GigaChat.__str__ = (
    lambda self: self.model
    + ("", " Lite")[self.model == "GigaChat"]
)
gigachat = GigaChat(
    credentials=config("GIGACHAT_AUTH_KEY"),
    model=config("GIGACHAT_MODEL"),
    verify_ssl_certs=False
)

EXTRACT_PROMPT = """
Ты эксперт в извлечении релевантной информации из текста.
Если значение атрибута неизвестно, поставь ему null.
"""

extract_prompt = ChatPromptTemplate.from_messages([
    ("system", EXTRACT_PROMPT),
    ("human", "{message}")
])

deposit_agent = ApiAgent(
    name="deposit_agent",
    mission="Рассчитать депозит с ежемесячной капитализацией процентов",
    examples=[
        "500k на полтора года под 7.2%",
        "на 6 мес. под 8%, сумма 1 млн.",
        "200 тысяч, 3 месяца, ставка 6"
    ],
    model=gigachat,
    prompt=extract_prompt,
    schema=DepositSchema,
    method="POST",
    url="https://compound-interest-calculator.containerapps.ru/standard",
    payload_name="json"
)

six_sigma_agent = ApiAgent(
    name="six_sigma_agent",
    mission="Оценить процесс по методике \"6 сигм\"",
    examples=[
        "total 100, nok 5, name Example Process",
        "ok 95, nok 5",
        "бракованных 5, всего 100",
        "пять дефектных из ста штук",
        "пять неудач из ста случаев",
        "из ста тестов пять провалены",
        "из сотни пять плохих, изделие - SSD",
        "хороших 95, всего 100",
        "из 100 результатов 95 успешных исходов"
    ],
    model=gigachat,
    prompt=extract_prompt,
    schema=SixSigmaSchema,
    method="GET",
    url="https://six-sigma.containerapps.ru/plot",
    payload_name="params"
)

# меню целевых агентов
menu = {
    agent.name: agent
    for _, agent in inspect.getmembers(sys.modules[__name__])
    if isinstance(agent, TargetAgent)
}

OFFTOP_SENTINEL = "offtop"

clf_prompt = f"""
Классифицируй сообщение как одно из {", ".join(menu)}.
Однако если невозможно выбрать класс уверенно или сообщение начинается с /,
ответь {OFFTOP_SENTINEL}.

Примеры:
{"\n\n".join(map(str, menu.values()))}
"""

supervisor = Supervisor(model=gigachat, prompt=clf_prompt)

missions = [agent.mission for agent in menu.values()]
fallback_answer = "\n\n".join([
    f"Я бот на базе {gigachat}, и вот что я могу:", *missions
])
