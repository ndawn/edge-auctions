FROM python:3.9-buster

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
#RUN poetry export -f requirements.txt --output requirements.txt
RUN poetry config virtualenvs.create false
#RUN pip install -r requirements.txt
RUN poetry install

#RUN apk del build-deps

ENTRYPOINT python3 -m auctions.app
