from auctions.config import Config
from auctions.db.models.auctions import Auction
from auctions.db.models.users import User
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.dependencies import Provide
from auctions.exceptions import ConflictError
from auctions.exceptions import NotAuthorizedError
from auctions.serializers.users import UserInfo
from auctions.services.password_service import PasswordService
from auctions.services.schedule_service import ScheduleService
from auctions.utils.insales import InsalesApi


class ShopConnectService:
    collate_fields = [
        "id",
        "email",
        "name",
        "surname",
        "phone",
        "client_group_id",
    ]

    def __init__(
        self,
        password_service: PasswordService = Provide(),
        schedule_service: ScheduleService = Provide(),
        auctions_repository: AuctionsRepository = Provide(),
        config: Config = Provide(),
    ) -> None:
        self.password_service = password_service
        self.schedule_service = schedule_service
        self.auctions_repository = auctions_repository
        self.config = config
        self.api = InsalesApi(
            self.config.shop_id,
            self.config.shop_api_key,
            self.config.shop_api_secret,
        )

    def get_user_info(self, user_id: int) -> dict[str, ...]:
        return self.api.get_client(user_id)

    def authenticate(self, login_data: dict[str, ...]) -> UserInfo:
        client = self.get_user_info(login_data["id"])

        for field in self.collate_fields:
            if field not in client or client[field] != login_data[field]:
                raise NotAuthorizedError("Invalid request")

        if client.get("default_address") is None or not client["default_address"].get("full_delivery_address"):
            raise ConflictError("Address is not set")

        return UserInfo.from_dict(client)

    def create_invoice(self, user: User, auctions: list[Auction]) -> None:
        shop_user_info = self.api.get_client(user.shop_id)

        shop_product_ids = []

        for auction in auctions:
            product_id = self.api.create_product(
                title=auction.item.name,
                category_id=self.config.shop_category_id,
                price=auction.get_last_bid().value,
            )

            shop_product_ids.append(product_id)

        order = self.api.create_order(
            product_ids=shop_product_ids,
            client=shop_user_info,
            shipping_address=shop_user_info.get("default_address"),
            delivery_variant_id=self.config.shop_delivery_variant_id,
            payment_gateway_id=self.config.shop_payment_gateway_id,
            status=self.config.shop_order_status_permalink,
        )

        for auction in auctions:
            self.auctions_repository.update(
                auction,
                invoice_id=order["id"],
                invoice_link=f"https://edgecomics.ru/orders/{order['key']}",
            )

    def check_invoice_paid(self, invoice_id: int) -> bool:
        try:
            order = self.api.get_order(invoice_id)
            return order.get("financial_status", "") == "paid"
        except InsalesApi.RequestFailedError as exception:
            return exception.status_code == 404
