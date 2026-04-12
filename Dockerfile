FROM python:3.12.0-alpine

COPY . /nexuscore/

RUN pip install -r /nexuscore/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/nexuscore/"

WORKDIR /nexuscore/src

CMD ["fastapi", "run", "--host", "0.0.0.0"]