FROM python:3.10

WORKDIR /tg_preparator

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -ms /bin/bash user

USER user

COPY main.py emoji.py config.py .

CMD ["python3", "main.py"]
