FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (can override at runtime)
ENV BOT_TOKEN=7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU
ENV PORT=8443

EXPOSE 8443

CMD ["python", "main.py"]
