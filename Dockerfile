FROM python:3.11-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY build/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/

# Устанавливаем рабочую директорию для запуска
WORKDIR /app/src/validation_service

# Запускаем приложение
CMD ["python", "main.py"] 