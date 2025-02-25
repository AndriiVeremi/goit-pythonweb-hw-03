FROM python:3.13

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p storage

EXPOSE 8000

CMD ["python", "main.py"]
