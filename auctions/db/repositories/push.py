from auctions.db.models.push import PushSubscription
from auctions.db.repositories.base import Repository


class PushSubscriptionsRepository(Repository[PushSubscription]):
    joined_fields = (
        PushSubscription.user,
    )

    @property
    def model(self) -> type[PushSubscription]:
        return PushSubscription
