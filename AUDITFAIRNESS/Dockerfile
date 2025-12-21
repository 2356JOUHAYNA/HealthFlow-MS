FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /app/reports /app/dashboards

EXPOSE 8050

CMD ["python", "app.py"]
