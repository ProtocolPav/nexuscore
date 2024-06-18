FROM python:3.10.8-buster

COPY requirements.txt /nexuscore/requirements.txt

RUN pip install -r /nexuscore/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/nexuscore/"

WORKDIR /nexuscore