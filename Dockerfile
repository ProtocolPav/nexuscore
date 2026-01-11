FROM python:3.12.0-alpine

COPY . /nexuscore/

RUN pip install -r /nexuscore/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/nexuscore/"

WORKDIR /nexuscore

CMD ["python", "-u", "nexus.py"]