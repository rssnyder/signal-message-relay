FROM python:3.12-slim

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN rm config.toml

ENTRYPOINT python main.py