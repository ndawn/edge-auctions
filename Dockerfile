FROM app_base

WORKDIR /app

COPY . .
COPY ./.env .

STOPSIGNAL SIGINT

ENTRYPOINT python3 -m auctions.app
