from typing import Callable

import dramatiq

# from auctions.db.models.enum import EmailType
from auctions.db.models.enum import PushEventType


class ScheduleService:
    @staticmethod
    def ensure_task(fn: Callable | dramatiq.Actor) -> dramatiq.Actor:
        if isinstance(fn, dramatiq.Actor):
            return fn

        return dramatiq.actor(fn)

    def send_push(self, recipient_id: str | None, event_type: PushEventType, payload: ...) -> None:
        from auctions.tasks import send_push
        self.ensure_task(send_push).send(recipient_id, event_type, payload)

    # @staticmethod
    # def send_email(recipient_id: str, message_type: EmailType) -> None:
    #     from auctions.tasks import send_email as send_email_task
    #     send_email_task.send(recipient_id, message_type)

    def create_invoice(self, user_id: str, auction_ids: list[int]) -> None:
        from auctions.tasks import create_invoice
        self.ensure_task(create_invoice).send(user_id, auction_ids)

    def check_invoices(self) -> None:
        from auctions.tasks import check_invoices
        self.ensure_task(check_invoices).send()

    def try_close_auction_sets(self) -> None:
        from auctions.tasks import try_close_auction_sets
        self.ensure_task(try_close_auction_sets).send()
