FROM python:3.8

COPY . /docker-exporter
WORKDIR /docker-exporter

RUN python3 -m pip install -r requirements.txt

ENTRYPOINT ["python3", "/docker-exporter/main.py"]
