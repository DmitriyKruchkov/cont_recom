FROM python:3.10

WORKDIR /web

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -ms /bin/bash user

USER user

COPY main.py .
COPY templates templates
COPY static static

CMD ["python3", "main.py"]