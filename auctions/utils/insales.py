import json
from base64 import b64encode

import loguru
import requests


class InsalesApi:
    class RequestFailedError(Exception):
        def __init__(self, error: ..., status_code: int) -> None:
            super().__init__(f"{status_code=}: {error}")
            self.error = error
            self.status_code = status_code

    def __init__(self, account: str, api_key: str, api_secret: str) -> None:
        self.account = account

        auth = b64encode(f"{api_key}:{api_secret}".encode("utf-8")).decode("utf-8")

        self.headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        }

        self.session = requests.session()

    def _build_full_url(self, url: str) -> str:
        url = url.removeprefix("/")
        return f"https://{self.account}.myinsales.ru/{url}"

    def request(self, method: str, url: str, data: dict[str, ...] = None) -> ...:
        loguru.logger.debug(f"Sending request to {url}")
        loguru.logger.debug(f"Request body: {data}")
        full_url = self._build_full_url(url)
        response = self.session.request(method=method, url=full_url, headers=self.headers, json=data)

        if response.status_code >= 400:
            raise self.RequestFailedError(response.text, response.status_code)

        return response.json()

    def get_client(self, client_id: int) -> dict[str, ...]:
        return self.request("GET", f"/admin/clients/{client_id}.json")

    def create_product(self, title: str, category_id: int, price: int) -> int:
        return self.request(
            "POST",
            "/admin/products.json",
            data={
                "product": {
                    "title": title,
                    "category_id": category_id,
                    "variants_attributes": [
                        {
                            "quantity": 1,
                            "price": price,
                        },
                    ],
                },
            },
        )["id"]

    def get_order(self, order_id: int) -> dict[str, ...]:
        return self.request("GET", f"/admin/orders/{order_id}.json")

    def create_order(
        self,
        product_ids: list[int],
        client: dict[str, ...],
        shipping_address: str,
        delivery_variant_id: int,
        payment_gateway_id: int,
        status: str,
    ) -> dict[str, ...]:
        return self.request(
            "POST",
            "/admin/orders.json",
            data={
                "order": {
                    "order_lines_attributes": [
                        {
                            "product_id": product_id,
                            "quantity": 1,
                            "vat": -1,
                        }
                        for product_id in product_ids
                    ],
                    "client": client,
                    "shipping_address_attributes": shipping_address,
                    "delivery_variant_id": delivery_variant_id,
                    "payment_gateway_id": payment_gateway_id,
                    "custom_status_permalink": status,
                }
            },
        )
