FROM app_base

WORKDIR /app

COPY . .

STOPSIGNAL SIGINT

ENTRYPOINT python3 -m auctions.app
