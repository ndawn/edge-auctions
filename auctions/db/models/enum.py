from enum import Enum


class AuthAppType(str, Enum):
    ADMIN = "admin"
    USER = "user"
    UNKNOWN = "unknown"


class ShopClientType(str, Enum):
    INDIVIDUAL = "Client::Individual"
    JURIDICAL = "Client::Juridical"


class PushEventType(str, Enum):
    AUCTION_DATE_DUE_UPDATED = "auctionDateDueUpdated"
    AUCTION_BID_CREATED = "auctionBidCreated"
    AUCTION_BID_BEATEN = "auctionBidBeaten"
    AUCTION_WON = "auctionWon"


class EmailType(str, Enum):
    WON_NO_ADDRESS = "won_no_address"


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
    OWN_BID = "ownBid"
    INVALID_BID = "invalidBid"
    INVALID_BUYOUT = "invalidBuyout"
    INVALID_BEATING = "invalidBeating"
    AUCTION_NOT_ACTIVE = "auctionNotActive"
