FROM app_base

WORKDIR /app

COPY . .

STOPSIGNAL SIGINT

CMD ["python3", "-m", "auctions.app"]
