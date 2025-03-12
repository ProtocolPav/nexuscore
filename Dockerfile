FROM python:3.11.8-alpine

COPY requirements.txt /nexuscore/requirements.txt

RUN pip install -r /nexuscore/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/nexuscore/"

WORKDIR /nexuscore