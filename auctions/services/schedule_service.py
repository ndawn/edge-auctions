from typing import Callable

import dramatiq
from flask import Flask

from auctions.db.models.enum import EmailType
from auctions.db.models.enum import PushEventType
from auctions.dependencies import Provide
from auctions.utils.app import with_app_context


class ScheduleService:
    def __init__(self, app: Flask = Provide()) -> None:
        self.app = app

    def ensure_task(self, fn: Callable | dramatiq.Actor) -> dramatiq.Actor:
        if not isinstance(fn, dramatiq.Actor):
            fn = dramatiq.actor(with_app_context(self.app)(fn))

        return fn

    def send_push(self, recipient_id: str | None, event_type: PushEventType, payload: ...) -> None:
        from auctions.tasks import send_push as send_push_task
        self.ensure_task(send_push_task).send(recipient_id, event_type, payload)

    def send_email(self, recipient_id: str, message_type: EmailType) -> None:
        from auctions.tasks import send_email as send_email_task
        self.ensure_task(send_email_task).send(recipient_id, message_type)

    def create_invoice(self, user_id: str, auction_ids: list[int]) -> None:
        from auctions.tasks import create_invoice as create_invoice_task
        self.ensure_task(create_invoice_task).send(user_id, auction_ids)

    def check_invoices(self) -> None:
        from auctions.tasks import check_invoices as check_invoices_task
        self.ensure_task(check_invoices_task).send()

    def try_close_auction_sets(self) -> None:
        from auctions.tasks import try_close_auction_sets as try_close_auction_sets_task
        self.ensure_task(try_close_auction_sets_task).send()
