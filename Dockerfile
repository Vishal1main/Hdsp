FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Optional: expose port 8080 (useful if webhook/server later)
EXPOSE 8080

CMD ["python", "main.py"]
