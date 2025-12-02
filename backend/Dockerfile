FROM python:3.12-slim

WORKDIR /root

RUN mkdir /root/travelcoin
WORKDIR /root/travelcoin

COPY *.py .
COPY *.txt .
COPY ./conf/* ./conf/

RUN apt-get update

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]

