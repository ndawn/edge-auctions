FROM app_base

WORKDIR /app

COPY . .

ENTRYPOINT python3 -m auctions.app
