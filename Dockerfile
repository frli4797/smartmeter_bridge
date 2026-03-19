FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY modbus_bridge.py ./
COPY homeassistant.yaml.example ./

EXPOSE 5020

CMD ["python", "modbus_bridge.py", "--config", "/app/homeassistant.yaml"]
