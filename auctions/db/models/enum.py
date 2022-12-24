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


class ExternalSource(Enum):
    VK = "VK"
    TELEGRAM = "TELEGRAM"


class ExternalTokenType(Enum):
    VK_USER = "VK_USER"
    VK_GROUP = "VK_GROUP"
    VK_SERVICE = "VK_SERVICE"
    TELEGRAM_BOT = "TELEGRAM_BOT"


class ExternalEntityRelatesTo(Enum):
    AUCTION = "auction"
    AUCTION_SET = "auction_set"
    AUCTION_TARGET = "auction_target"
    BIDDER = "bidder"
    BID = "bid"


class CreateBidFailReason(Enum):
    INVALID_BID = "invalid_bid"
    INVALID_BUYOUT = "invalid_buyout"
    INVALID_BEATING = "invalid_beating"
    AUCTION_NOT_ACTIVE = "auction_not_active"


class VKCallbackEventType(Enum):
    SERVER_CONFIRMATION = "confirmation"
    MESSAGE_EVENT = "message_event"
    MESSAGE_NEW = "message_new"
    PHOTO_NEW = "photo_new"
    PHOTO_COMMENT_NEW = "photo_comment_new"
    PHOTO_COMMENT_EDIT = "photo_comment_edit"
    PHOTO_COMMENT_DELETE = "photo_comment_delete"
    PHOTO_COMMENT_RESTORE = "photo_comment_restore"


class VKIntentType(Enum):
    DEFAULT = "default"
    CONFIRMED_NOTIFICATION = "confirmed_notification"


class VKCallbackMessageEventCommandType(Enum):
    INTERNAL_COMMAND = "internal_command"


class VKCallbackMessageEventPayloadActionType(Enum):
    INTENT_SUBSCRIBE = "intent_subscribe"
    INTENT_UNSUBSCRIBE = "intent_unsubscribe"
