from functools import wraps
from typing import Callable

import dramatiq

from auctions.db.models.enum import PushEventType


class ScheduleService:
    @staticmethod
    def actor_mimic(func: Callable) -> Callable:
        @wraps(func)
        def decorated(*args, **kwargs) -> ...:
            return dramatiq.actor(func).send(*args, **kwargs)

        return decorated

    @staticmethod
    @actor_mimic
    def send_push(recipient_id: str | None, event_type: PushEventType, payload: ...) -> None:
        ...

    @staticmethod
    @actor_mimic
    def create_invoice(user_id: str, auction_ids: list[int]) -> None:
        ...

    @staticmethod
    @actor_mimic
    def check_invoices() -> None:
        ...

    @staticmethod
    @actor_mimic
    def try_close_auction_sets() -> None:
        ...
