from auctions.db.models.enum import SupplyItemParseStatus
from auctions.db.models.images import Image
from auctions.db.models.item_types import ItemType
from auctions.db.models.items import Item
from auctions.db.models.sessions import SupplySession
from auctions.db.repositories.item_types import ItemTypesRepository
from auctions.db.repositories.images import ImagesRepository
from auctions.db.repositories.items import ItemsRepository
from auctions.db.repositories.sessions import SupplySessionsRepository
from auctions.dependencies import injectable
from auctions.exceptions import BadRequestError
from auctions.exceptions import ItemProcessingFailed
from auctions.exceptions import SessionApplyFailed
from auctions.services.images_service import ImagesService
from auctions.services.parse_service import ParseService


@injectable
class SupplyService:
    def __init__(
        self,
        images_service: ImagesService,
        parse_service: ParseService,
        images_repository: ImagesRepository,
        item_types_repository: ItemTypesRepository,
        items_repository: ItemsRepository,
        supply_sessions_repository: SupplySessionsRepository,
    ) -> None:
        self.images_service = images_service
        self.parse_service = parse_service
        self.images_repository = images_repository
        self.item_types_repository = item_types_repository
        self.items_repository = items_repository
        self.supply_sessions_repository = supply_sessions_repository

    def get_current_session(self) -> SupplySession | None:
        return self.supply_sessions_repository.get_current_session()

    def start_session(self, item_type: ItemType, images: list[Image]) -> SupplySession:
        session = self.supply_sessions_repository.create(item_type=item_type, total_items=len(images))

        for image in images:
            self.items_repository.create(
                session=session,
                images=[image],
                type=item_type,
                price_category=item_type.price_category,
                wrap_to=item_type.wrap_to,
            )

        return session

    def process_item(self, item: Item) -> Item:
        if item.session is None:
            raise ItemProcessingFailed('Cannot process an already applied item')

        return self.parse_service.process_item(item)

    def add_images(self, session: SupplySession, images: list[Image]) -> list[Item]:
        items = []

        for image in images:
            self.items_repository.create(session=session, images=[image], wrap_to=session.item_type.wrap_to)

        session.total_items += len(items)
        self.supply_sessions_repository.refresh(session)
        return items

    def join_items(self, item_to_keep: Item, item_to_drop: Item, images: list[Image], main_image: Image) -> Item:
        if main_image not in images:
            raise BadRequestError("Main image must be in the list of selected images", status_code=422)

        image_ids = [image.id for image in images]
        images_to_delete = [image for image in item_to_keep.images + item_to_drop.images if image.id not in image_ids]
        self.images_repository.delete(images_to_delete)

        for image in images:
            image.item = item_to_keep
            image.is_main = image.id == main_image.id

        self.items_repository.delete([item_to_drop])
        return item_to_keep

    def apply_session(self) -> list[Item]:
        session = self.get_current_session()

        items = session.items[:]

        for item in items:
            if item.parse_status != SupplyItemParseStatus.SUCCESS:
                raise SessionApplyFailed("Cannot apply a session with items not parsed successfully")

            item.session = None
            item.session_id = None

        self.supply_sessions_repository.delete([session])
        return items

    def discard_session(self) -> None:
        session = self.get_current_session()

        for item in session.items:
            self.images_service.delete_for_item(item)
            self.items_repository.delete([item])

        self.supply_sessions_repository.delete([session])
