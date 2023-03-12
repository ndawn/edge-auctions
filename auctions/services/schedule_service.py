from typing import Callable

import dramatiq

from auctions.db.models.enum import EmailType
from auctions.db.models.enum import PushEventType


class ScheduleService:
    @staticmethod
    def send_push(recipient_id: str | None, event_type: PushEventType, payload: ...) -> None:
        from auctions.tasks import send_push as send_push_task
        send_push_task.send(recipient_id, event_type, payload)

    @staticmethod
    def send_email(recipient_id: str, message_type: EmailType) -> None:
        from auctions.tasks import send_email as send_email_task
        send_email_task.send(recipient_id, message_type)

    @staticmethod
    def create_invoice(user_id: str, auction_ids: list[int]) -> None:
        from auctions.tasks import create_invoice as create_invoice_task
        create_invoice_task.send(user_id, auction_ids)

    @staticmethod
    def check_invoices() -> None:
        from auctions.tasks import check_invoices as check_invoices_task
        check_invoices_task.send()

    @staticmethod
    def try_close_auction_sets() -> None:
        from auctions.tasks import try_close_auction_sets as try_close_auction_sets_task
        try_close_auction_sets_task.send()
