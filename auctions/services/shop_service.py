from auctions.config import Config
from auctions.db.models.shop import ShopInfo
from auctions.db.repositories.shop import ShopInfoRepository
from auctions.dependencies import Provide
from auctions.exceptions import ForbiddenError
from auctions.services.password_service import PasswordService


class ShopService:
    def __init__(
        self,
        password_service: PasswordService = Provide(),
        shop_info_repository: ShopInfoRepository = Provide(),
        config: Config = Provide(),
    ) -> None:
        self.password_service = password_service
        self.shop_info_repository = shop_info_repository
        self.config = config

    def get_shop_by_id(self, shop_id: int) -> ShopInfo:
        return self.shop_info_repository.get_one_by_id(shop_id)

    def install_shop(self, shop_id: int, shop_name: str, token: str) -> ShopInfo:
        password = self.password_service.generate_shop_password(token)

        return self.shop_info_repository.create(
            id=shop_id,
            name=shop_name,
            password=password,
        )

    def uninstall_shop(self, shop_id: int, shop_name: str, password: str) -> None:
        shop = self.shop_info_repository.get_one_by_id(shop_id)

        if self.config.shop_secret != password:
            raise ForbiddenError()

        self.shop_info_repository.delete([shop])
