FROM python:3.12.7-alpine3.20
LABEL maintainer="eimeredelin@sberbank.ru"
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["python", "app/main.py"]
