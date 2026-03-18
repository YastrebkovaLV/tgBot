FROM ubuntu:latest
LABEL authors="liliaastrebkova"

ENTRYPOINT ["top", "-b"]

# Базовый образ Python
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем только requirements сначала (для кеша)
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запуск бота
CMD ["python", "bot.py"]