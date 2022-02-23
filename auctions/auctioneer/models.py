from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, UUID4
from tortoise import fields

from auctions.comics.models import PyItemWithImages
from auctions.utils.abstract_models import (
    CreatedRecordedModel,
    CreatedUpdatedRecordedModel,
    PyCreatedRecordedModel,
    PyCreatedUpdatedRecordedModel,
)


class AuctionCloseCodeType(Enum):
    CLOSED = 'closed'
    ALREADY_CLOSED = 'already_closed'
    NOT_CLOSED_YET = 'not_closed_yet'
    NOT_STARTED_YET = 'not_started_yet'


class BidValidationResult(Enum):
    VALID_BID = 'valid_bid'
    VALID_BUYOUT = 'valid_buyout'
    INVALID_BID = 'invalid_bid'
    INVALID_BEATING = 'invalid_beating'
    INVALID_BUYOUT = 'invalid_buyout'


class ExternalSource(CreatedUpdatedRecordedModel):
    code = fields.CharField(pk=True, max_length=255)
    name = fields.CharField(max_length=255)


class AuctionTarget(CreatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)

    external: fields.ReverseRelation["ExternalAuctionTarget"]

    async def get_external(self, source: ExternalSource) -> "ExternalAuctionTarget":
        return await self.external.filter(source=source).get()

    async def has_external(self, source: ExternalSource) -> bool:
        return await self.external.filter(source=source).exists()


class ExternalAuctionTarget(CreatedRecordedModel):
    target = fields.ForeignKeyField('auctioneer.AuctionTarget', related_name='external', on_delete=fields.CASCADE)
    source = fields.ForeignKeyField('auctioneer.ExternalSource', on_delete=fields.RESTRICT)
    entity_id = fields.IntField(unique=True)


class AuctionSet(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    target = fields.ForeignKeyField('auctioneer.AuctionTarget', on_delete=fields.RESTRICT)
    date_due = fields.DatetimeField()
    anti_sniper = fields.IntField()
    started = fields.DatetimeField(null=True)
    ended = fields.DatetimeField(null=True)

    auctions: fields.ReverseRelation["Auction"]
    external: fields.ReverseRelation["ExternalAuctionSet"]

    async def get_external(self, source: ExternalSource) -> "ExternalAuctionSet":
        return await self.external.filter(source=source).get()

    async def has_external(self, source: ExternalSource) -> bool:
        return await self.external.filter(source=source).exists()


class ExternalAuctionSet(CreatedUpdatedRecordedModel):
    set = fields.ForeignKeyField('auctioneer.AuctionSet', related_name='external', on_delete=fields.CASCADE)
    source = fields.ForeignKeyField('auctioneer.ExternalSource', on_delete=fields.RESTRICT)
    entity_id = fields.IntField()


class Auction(CreatedUpdatedRecordedModel):
    uuid = fields.UUIDField(pk=True)
    set = fields.ForeignKeyField('auctioneer.AuctionSet', on_delete=fields.CASCADE)
    item = fields.OneToOneField('comics.Item', on_delete=fields.RESTRICT)
    date_due = fields.DatetimeField()
    buy_now_price = fields.IntField(null=True)
    buy_now_expires = fields.IntField(null=True)
    bid_start_price = fields.IntField(default=0)
    bid_min_step = fields.IntField(default=0)
    bid_multiple_of = fields.IntField(default=0)
    is_active = fields.BooleanField(default=True)
    started = fields.DatetimeField(null=True)
    ended = fields.DatetimeField(null=True)

    bids: fields.ReverseRelation["Bid"]
    external: fields.ReverseRelation["ExternalAuction"]

    async def get_external(self, source: ExternalSource) -> "ExternalAuction":
        return await self.external.filter(source=source).get()

    async def has_external(self, source: ExternalSource) -> bool:
        return await self.external.filter(source=source).exists()

    async def get_last_bid(self) -> Optional["Bid"]:
        return await self.bids.filter(next_bid=None).get_or_none()

    async def get_bidders(self) -> list["Bidder"]:
        return list(set(bid.bidder for bid in await self.bids.all().select_related('bidder')))


class ExternalAuction(CreatedUpdatedRecordedModel):
    auction = fields.ForeignKeyField('auctioneer.Auction', related_name='external', on_delete=fields.CASCADE)
    source = fields.ForeignKeyField('auctioneer.ExternalSource', on_delete=fields.RESTRICT)
    entity_id = fields.IntField()


class Bidder(CreatedUpdatedRecordedModel):
    target = fields.ForeignKeyField('auctioneer.AuctionTarget', related_name='bidders', on_delete=fields.RESTRICT)
    last_name = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    avatar = fields.TextField(null=True)

    bids: fields.ReverseRelation["Bid"]
    external: fields.ReverseRelation["ExternalBidder"]

    @classmethod
    async def get_or_create_from_external(
        cls,
        subject_id: int,
        source: ExternalSource,
        target: AuctionTarget,
    ) -> tuple["Bidder", bool]:
        external_bidder = await ExternalBidder.get_or_none(
            subject_id=subject_id,
            bidder__target=target,
        ).select_related('bidder')

        if external_bidder is None:
            bidder = await cls.create(last_name='', first_name='', target=target)
            await ExternalBidder.create(bidder=bidder, subject_id=subject_id, source=source)
            return bidder, True

        return external_bidder.bidder, False

    async def get_external(self, source: ExternalSource) -> "ExternalBidder":
        return await self.external.filter(source=source).get()

    async def has_external(self, source: ExternalSource) -> bool:
        return await self.external.filter(source=source).exists()

    async def has_unclosed_auctions(self, set: AuctionSet) -> bool:
        return await self.bids.filter(auction__is_active=True, auction__set_id=set.uuid).exists()

    async def get_won_auctions(self, set: AuctionSet) -> list["Auction"]:
        return [
            bid.auction
            for bid in await self.bids.filter(
                next_bid=None,
                auction__is_active=False,
                auction__set_id=set.uuid,
            ).select_related('auction')
        ]

    async def get_won_amount(self, set: AuctionSet) -> int:
        bids = await self.bids.filter(next_bid=None, auction__is_active=False, auction__set_id=set.uuid)
        return sum([bid.value for bid in bids])


class ExternalBidder(CreatedUpdatedRecordedModel):
    bidder = fields.ForeignKeyField('auctioneer.Bidder', related_name='external', on_delete=fields.CASCADE)
    source = fields.ForeignKeyField('auctioneer.ExternalSource', on_delete=fields.RESTRICT)
    subject_id = fields.IntField()


class Bid(CreatedRecordedModel):
    bidder = fields.ForeignKeyField('auctioneer.Bidder', on_delete=fields.RESTRICT)
    auction = fields.ForeignKeyField('auctioneer.Auction', related_name='bids', on_delete=fields.CASCADE)
    value = fields.IntField()
    is_sniped = fields.BooleanField(default=False)
    is_buyout = fields.BooleanField(default=False)
    next_bid = fields.ForeignKeyField('auctioneer.Bid', on_delete=fields.SET_NULL, null=True, default=None)

    external: fields.OneToOneNullableRelation["ExternalBid"]

    async def get_previous(self) -> Optional["Bid"]:
        return await Bid.get_or_none(next_bid=self)

    async def get_external(self, source: ExternalSource) -> Optional["ExternalBid"]:
        external = await self.external

        if external is None or external.source_id != source.code:
            return None

        return external

    async def has_external(self, source: ExternalSource) -> bool:
        return await self.external is not None and (await self.external).source_id == source.code


class ExternalBid(CreatedRecordedModel):
    bid = fields.OneToOneField('auctioneer.Bid', related_name='external', on_delete=fields.CASCADE)
    source = fields.ForeignKeyField('auctioneer.ExternalSource', on_delete=fields.RESTRICT)
    entity_id = fields.IntField()


# ==========================================================
#   _______     _______          _   _ _______ _____ _____
#  |  __ \ \   / /  __ \   /\   | \ | |__   __|_   _/ ____|
#  | |__) \ \_/ /| |  | | /  \  |  \| |  | |    | || |
#  |  ___/ \   / | |  | |/ /\ \ | . ` |  | |    | || |
#  | |      | |  | |__| / ____ \| |\  |  | |   _| || |____
#  |_|      |_|  |_____/_/    \_\_| \_|  |_|  |_____\_____|
# ==========================================================


class PyExternalSource(PyCreatedUpdatedRecordedModel):
    code: str
    name: str

    class Config:
        orm_mode = True


class PyExternalSourceIn(BaseModel):
    code: Optional[str]
    name: str


class PyExternalAuctionTarget(PyCreatedRecordedModel):
    id: int
    source: PyExternalSource
    entity_id: int

    class Config:
        orm_mode = True


class PyAuctionTarget(PyCreatedRecordedModel):
    uuid: UUID4
    name: str
    external: list[PyExternalAuctionTarget]

    class Config:
        orm_mode = True


class PyExternalAuctionTargetIn(BaseModel):
    id: Optional[int]
    source_id: Optional[str]
    entity_id: Optional[int]


class PyAuctionTargetIn(BaseModel):
    name: Optional[str]
    external: list[PyExternalAuctionTargetIn]


class PyAuctionSet(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    target: PyAuctionTarget
    date_due: datetime
    anti_sniper: int
    started: Optional[datetime]
    ended: Optional[datetime]

    class Config:
        orm_mode = True


class PyAuctionSetCreateQuantitySingle(BaseModel):
    price_category_id: int
    quantity: int


class PyAuctionSetCreateQuantity(BaseModel):
    item_type_id: int
    prices: list[PyAuctionSetCreateQuantitySingle]


class PyAuctionSetCreate(BaseModel):
    target_uuid: UUID4
    date_due: datetime
    anti_sniper: int
    quantities: list[PyAuctionSetCreateQuantity]


class PyExternalAuctionSet(PyCreatedUpdatedRecordedModel):
    id: int
    set: PyAuctionSet
    source: PyExternalSource
    entity_id: int


class PyExternalAuctionSetOut(PyCreatedUpdatedRecordedModel):
    id: int
    source: PyExternalSource
    entity_id: int


class PyAuctionSetCreateOut(BaseModel):
    uuid: UUID4
    target_uuid: UUID4
    date_due: datetime
    anti_sniper: int
    items: list[dict]


class PyAuction(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    item: PyItemWithImages
    is_active: bool

    class Config:
        orm_mode = True


class PyExternalAuction(PyCreatedUpdatedRecordedModel):
    auction: PyAuction
    source: PyExternalSource
    entity_id: int


class PyExternalAuctionOut(PyCreatedUpdatedRecordedModel):
    id: int
    source: PyExternalSource
    entity_id: int


class PyAuctionOut(PyCreatedUpdatedRecordedModel):
    uuid: UUID4
    item: PyItemWithImages
    date_due: datetime
    buy_now_price: Optional[int]
    buy_now_expires: Optional[int]
    bid_start_price: int
    bid_min_step: int
    bid_multiple_of: int
    is_active: bool


class PyAuctionOutWithSet(PyAuctionOut):
    set: PyAuctionSet


class PyAuctionOutWithExternal(PyAuctionOut):
    external: list[PyExternalAuctionOut]


class PyAuctionSetOut(PyAuctionSet):
    auctions: list[PyAuctionOutWithExternal]
    external: list[PyExternalAuctionSetOut]


class PyAuctionSetOutWithTotalEarned(PyAuctionSetOut):
    total_earned: int


class PyAuctionRerollIn(BaseModel):
    item_type_id: int
    price_category_id: int


class PyBidder(PyCreatedUpdatedRecordedModel):
    id: int
    last_name: Optional[str]
    first_name: Optional[str]
    avatar: Optional[str]

    class Config:
        orm_mode = True


class PyExternalBidder(PyCreatedUpdatedRecordedModel):
    id: int
    source: PyExternalSource
    subject_id: int

    class Config:
        orm_mode = True


class PyExternalBidderOut(PyCreatedUpdatedRecordedModel):
    id: int
    bidder: PyBidder
    source: PyExternalSource
    subject_id: int


class PyBidderOut(PyCreatedUpdatedRecordedModel):
    id: int
    last_name: Optional[str]
    first_name: Optional[str]
    avatar: Optional[str]
    external: list[PyExternalBidderOut]


class PyBid(PyCreatedRecordedModel):
    id: int
    bidder: PyBidder
    value: int
    is_sniped: bool
    is_buyout: bool
    next_bid: Optional["PyBid"]

    class Config:
        orm_mode = True


class PyBidWithExternal(PyCreatedRecordedModel):
    id: int
    bidder: PyBidder
    value: int
    is_sniped: bool
    is_buyout: bool
    next_bid: Optional["PyBidWithExternal"]
    external: Optional["PyExternalBid"]

    class Config:
        orm_mode = True


class PyAuctionOutWithBids(PyAuctionOut):
    bids: list[PyBidWithExternal]


class PyAuctionOutWithExternalAndBids(PyAuctionOutWithBids, PyAuctionOutWithExternal):
    pass


class PyAuctionOutFull(PyAuctionOutWithSet, PyAuctionOutWithExternalAndBids):
    set: PyAuctionSet


class PyExternalBid(PyCreatedRecordedModel):
    id: int
    source: PyExternalSource
    entity_id: int

    class Config:
        orm_mode = True


class PyExternalBidOut(PyCreatedRecordedModel):
    id: int
    bid: PyBid
    source: PyExternalSource
    entity_id: int


class PyBidOut(PyCreatedRecordedModel):
    id: int
    bidder: PyBidder
    auction: PyAuction
    value: int
    is_sniped: bool
    is_buyout: bool
    next_bid: Optional["PyBidOut"]
    external: Optional[PyExternalBidOut]


class InvalidBid(BaseModel):
    id: Optional[int]
    value: str
    auction: Auction
    external_auction: Optional[ExternalAuction]
    target: Optional[ExternalAuctionTarget]
    source: Optional[ExternalSource]

    class Config:
        arbitrary_types_allowed = True


class PyAuctionCreateIn(BaseModel):
    ...


class PyBidCreateIn(BaseModel):
    value: int
    bidder_id: int


class PyExternalBidCreateIn(BaseModel):
    value: int
    bid_id: int
    bidder_id: int


class PyAuctionCloseOut(BaseModel):
    auction_id: str
    code: AuctionCloseCodeType
    retry_at: Optional[int]


class PyAuctionSetCloseOut(BaseModel):
    uuid: str
    ended: Optional[datetime]
    auction_statuses: list[PyAuctionCloseOut]


class PyAuctionSetExportOut(BaseModel):
    url: str
