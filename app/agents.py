__all__ = [
    "menu", "supervisor",
    "OFFTOP_SENTINEL", "fallback_answer"
]

# стандартная библиотека
import os

# сторонние библиотеки
from langchain_core.prompts import ChatPromptTemplate
from langchain_gigachat.chat_models import GigaChat

# пользовательские модули
from models import *


OFFTOP_SENTINEL = "offtop"


GigaChat.__str__ = (
    lambda self: self.model
    + ("", " Lite")[self.model == "GigaChat"]
)
gigachat = GigaChat(
    credentials=os.environ["GIGACHAT_AUTH_KEY"],
    model=os.environ["GIGACHAT_MODEL"],
    verify_ssl_certs=False
)

extractor_sys_prompt = """
Ты эксперт в извлечении релевантной информации из текста.
Если значение атрибута неизвестно, поставь ему null.
"""

extract_prompt = ChatPromptTemplate.from_messages([
    ("system", extractor_sys_prompt),
    ("human", "{message}")
])

deposit_agent = ApiAgent(
    mission="Рассчитать депозит с ежемесячной капитализацией процентов",
    examples=[
        ("500k на полтора года под 7.2%", "deposit_agent"),
        ("на 6 мес. под 8%, сумма 1 млн.", "deposit_agent"),
        ("200 тысяч, 3 месяца, ставка 6", "deposit_agent")
    ],
    model=gigachat,
    prompt=extract_prompt,
    schema=DepositSchema,
    method="POST",
    url="https://compound-interest-calculator.containerapps.ru/standard",
    payload_name="json"
)

six_sigma_agent = ApiAgent(
    mission="Оценить процесс по методике \"6 сигм\"",
    examples=[
        ("total 100, nok 5, name Example Process", "six_sigma_agent"),
        ("ok 95, nok 5", "six_sigma_agent"),
        ("бракованных 5, всего 100", "six_sigma_agent"),
        ("пять дефектных из ста штук", "six_sigma_agent"),
        ("пять неудач из ста случаев", "six_sigma_agent"),
        ("из ста тестов пять провалены", "six_sigma_agent"),
        ("из сотни пять плохих, изделие - SSD", "six_sigma_agent"),
        ("хороших 95, всего 100", "six_sigma_agent"),
        ("из 100 результатов 95 успешных исходов", "six_sigma_agent")
    ],
    model=gigachat,
    prompt=extract_prompt,
    schema=SixSigmaSchema,
    method="GET",
    url="https://six-sigma.containerapps.ru/chart",
    payload_name="params"
)

######## меню целевых агентов ########
menu = {
    "deposit_agent"  : deposit_agent,
    "six_sigma_agent": six_sigma_agent
}
######################################

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
