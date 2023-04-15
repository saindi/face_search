FROM python:3.8

RUN apt-get -y update && \
    apt-get install -y --fix-missing \
    cmake \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /face_search

RUN pip install --upgrade pip
COPY requirements.txt /face_search/
RUN pip install -r requirements.txt

COPY . /face_search/
