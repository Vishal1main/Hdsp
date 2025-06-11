FROM python:3.9-slim

WORKDIR /app

# पहले requirements.txt कॉपी करें
COPY requirements.txt .

# Dependencies इंस्टॉल करें
RUN pip install --no-cache-dir -r requirements.txt

# अब सारी फाइल्स कॉपी करें
COPY . .

# Verify files
RUN ls -la  # Debugging के लिए

CMD ["python", "bot.py"]
