FROM python:3.11-slim-bullseye

# RUN apt update && apt install -y procps gdb

# Add the `ls` alias to simplify debugging
RUN echo "alias ll='/bin/ls -l --color=auto'" >> /root/.bashrc

ENV ANTAREST_CONF /resources/application.yaml

RUN mkdir -p examples/studies

COPY ./requirements.txt ./conf/* /conf/
COPY ./antarest /antarest
COPY ./resources /resources
COPY ./scripts /scripts
COPY ./alembic /alembic
COPY ./alembic.ini /alembic.ini

RUN pip3 install --no-cache-dir --upgrade pip && pip3 install --no-cache-dir -r /conf/requirements.txt

ENTRYPOINT ["./scripts/start.sh"]
