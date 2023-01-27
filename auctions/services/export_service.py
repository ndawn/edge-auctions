from io import BytesIO

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from auctions.db.models.auctions import Auction
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.users import UsersRepository
from auctions.dependencies import Provide


class ExportService:
    def __init__(
        self,
        auctions_repository: AuctionsRepository = Provide(),
        users_repository: UsersRepository = Provide(),
    ) -> None:
        self.auctions_repository = auctions_repository
        self.users_repository = users_repository

        self.empty_fields = {
            "ID": lambda auction: auction.id,
            "Название": lambda auction: auction.item.name,
            "UPC": lambda auction: (auction.item.upca or "") + (auction.item.upc5 or ""),
        }

        # self.winners_fields = {
        #     "ID": lambda bidder: bidder.id,
        #     "Имя": lambda bidder: f"{bidder.first_name} {bidder.last_name}",
        #     ""
        # }

    def export_empty_auctions(self, set_id: int) -> bytes:
        empty_auctions = self.auctions_repository.get_many((Auction.set_id == set_id) & ~Auction.bids.any())

        content_buffer = BytesIO()

        workbook = Workbook()
        worksheet: Worksheet = workbook.active

        worksheet.append(list(self.empty_fields.keys()))

        for auction in empty_auctions:
            worksheet.append(field(auction) for name, field in self.empty_fields.items())

        workbook.save(content_buffer)

        return content_buffer.getvalue()

    # def export_auction_winners(self, set_id: int) -> bytes:
    #     auction_winners = self.bidders_repository.get_many((Auction.set_id == set_id) & ~Auction.bids.any())
    #
    #     content_buffer = BytesIO()
    #
    #     workbook = Workbook()
    #     worksheet: Worksheet = workbook.active
    #
    #     worksheet.append(self.empty_fields.keys())
    #
    #     for auction in empty_auctions:
    #         worksheet.append(field(auction) for name, field in self.empty_fields.items())
    #
    #     workbook.save(content_buffer)
    #
    #     return content_buffer.getvalue()
