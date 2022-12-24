from datetime import datetime

from auctions.db.models.enum import CreateBidFailReason


class HTTPError(Exception):
    default_message: str = "An error occurred while processing the request"
    default_status_code: int = 500

    def __init__(self, message: str = None, status_code: int = None, extra: dict = None) -> None:
        super().__init__()
        self.message = message or self.default_message
        self.status_code = status_code or self.default_status_code
        self.extra = extra or {}


class BadRequestError(HTTPError):
    default_message: str = "Bad request"
    default_status_code: int = 400


class NotAuthorizedError(HTTPError):
    default_message: str = "User is not authenticated"
    default_status_code: int = 401


class ForbiddenError(HTTPError):
    default_message: str = "Forbidden"
    default_status_code: int = 403


class NotFoundError(HTTPError):
    default_message = str = "Not found"
    default_status_code = int = 404


class ConflictError(HTTPError):
    default_message = str = "Conflict"
    default_status_code = int = 409


class ObjectDoesNotExist(NotFoundError):
    default_message: str = "Object does not exist"


class UserNotAuthenticatedError(NotAuthorizedError):
    default_message: str = "User is not authenticated"


class ValidationError(BadRequestError):
    default_message: str = "Validation error"
    default_status_code = 422


class ItemProcessingFailed(BadRequestError):
    default_message: str = "Item processing failed"


class UserDoesNotExist(NotAuthorizedError):
    default_message: str = "User does not exist"


class UserIsNotPermittedToAuthWithPassword(NotAuthorizedError):
    default_message: str = "User is not permitted to authenticate using password"


class UserAlreadyExists(ConflictError):
    default_message: str = "User already exists"


class InvalidPassword(NotAuthorizedError):
    default_message: str = "Invalid password"


class InvalidSignature(NotAuthorizedError):
    default_message: str = "Invalid signature"


class InvalidAuthToken(NotAuthorizedError):
    default_message: str = "Auth token is invalid or expired"


class ExternalEntityDoesNotExist(ObjectDoesNotExist):
    default_message: str = "External entity does not exist"
    default_status_code: int = 500

    def __init__(self, source: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.message = f"{self.default_message} for source {source}"


class MainImageDoesNotExist(ObjectDoesNotExist):
    default_message: str = "Main image does not exist"
    default_status_code: int = 500


class TooManyImages(ConflictError):
    default_message: str = "Too many images"


class SessionStartFailed(ConflictError):
    default_message: str = "Session start failed"


class SessionApplyFailed(ConflictError):
    default_message: str = "Session apply failed"


class AuctionSetStartFailed(ConflictError):
    default_message: str = "Auction set is already started or ended"


class AuctionSetEndFailed(ConflictError):
    default_message: str = "Auction set is already ended"


class AuctionCloseFailed(ConflictError):
    default_message: str = "Auction is already ended or is not started yet"


class AuctionReschedule(Exception):
    def __init__(self, execute_at: datetime):
        Exception.__init__(self)
        self.execute_at = execute_at


class CreateBidFailed(ConflictError):
    default_message: str = "Bid creation failed"

    def __init__(self, reason: CreateBidFailReason, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.message = self.default_message
        self.reason = reason
