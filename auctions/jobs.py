from auctions.services.schedule_service import ScheduleService


def periodic_auction_set_check() -> None:
    ScheduleService.try_close_auction_sets()


def periodic_invoice_check() -> None:
    ScheduleService.check_invoices()
