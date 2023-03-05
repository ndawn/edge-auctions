from auctions.dependencies import inject
from auctions.dependencies import Provide
from auctions.services.schedule_service import ScheduleService


@inject
def periodic_auction_set_check(schedule_service: ScheduleService = Provide()) -> None:
    schedule_service.try_close_auction_sets()


@inject
def periodic_invoice_check(schedule_service: ScheduleService = Provide()) -> None:
    schedule_service.check_invoices()
