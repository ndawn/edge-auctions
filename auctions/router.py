from fastapi.routing import APIRouter

from auctions.accounts.endpoints import router as accounts_router
from auctions.auctioneer.endpoints import router as auctioneer_router
from auctions.comics.endpoints import router as comics_router
from auctions.supply.endpoints import router as supply_router


router = APIRouter(redirect_slashes=False)
router.include_router(accounts_router, prefix='/accounts')
router.include_router(auctioneer_router, prefix='/auctioneer')
router.include_router(comics_router, prefix='/comics')
router.include_router(supply_router, prefix='/supply')
