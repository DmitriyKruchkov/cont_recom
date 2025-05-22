FROM python:3.10

WORKDIR /ml_topics

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -ms /bin/bash user

USER user

COPY main.py templates .

CMD ["python3", "main.py"]