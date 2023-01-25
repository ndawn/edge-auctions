from enum import Enum


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class SupplyItemParseStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class AuctionCloseCodeType(Enum):
    CLOSED = "closed"
    ALREADY_CLOSED = "already_closed"
    NOT_CLOSED_YET = "not_closed_yet"
    NOT_STARTED_YET = "not_started_yet"


class BidValidationResult(Enum):
    VALID_BID = "valid_bid"
    VALID_BUYOUT = "valid_buyout"
    INVALID_BID = "invalid_bid"
    INVALID_BEATING = "invalid_beating"
    INVALID_BUYOUT = "invalid_buyout"


class CreateBidFailReason(Enum):
    INVALID_BID = "invalid_bid"
    INVALID_BUYOUT = "invalid_buyout"
    INVALID_BEATING = "invalid_beating"
    AUCTION_NOT_ACTIVE = "auction_not_active"
