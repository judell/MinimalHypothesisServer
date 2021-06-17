FROM python:3.7-alpine

WORKDIR /MinimalHypothesisServer

RUN pip install pyramid

COPY ./service.py .
COPY ./annotation.db .

EXPOSE 4000
CMD ["python3", "service.py"]


