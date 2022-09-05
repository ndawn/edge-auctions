FROM python:3.9-slim

COPY . /app
WORKDIR /app

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-dev \
    musl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libjpeg-dev \
    libzbar-dev

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install

ENTRYPOINT python3 -m auctions.app
