FROM python:3.8-slim-buster

ENV ANTAREST_CONF /resources/application.yaml
ENV UVICORN_WORKERS 8
ENV UVICORN_ROOT_PATH /
ENV UVICORN_TIMEOUT 60

RUN mkdir -p examples/studies

WORKDIR /app

COPY ./requirements.txt /conf/
COPY ./antarest /antarest
COPY ./resources /resources
COPY ./scripts /scripts
COPY ./alembic /alembic
COPY ./alembic.ini /alembic.ini

COPY ./antares-launcher /antares-launcher
RUN ln -s /antares-launcher/antareslauncher /antareslauncher
RUN mkdir /conf/antares-launcher
RUN cp /antares-launcher/requirements.txt /conf/antares-launcher/requirements.txt

RUN pip3 install --upgrade pip \
    && pip3 install -r /app/conf/requirements.txt

ENTRYPOINT ./scripts/start.sh
