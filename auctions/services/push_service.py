import json
from dataclasses import asdict
from traceback import print_exception

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from auctions.config import Config
from auctions.db.models.enum import PushEventType
from auctions.db.models.push import PushSubscription
from auctions.db.models.users import User
from auctions.db.repositories.push import PushSubscriptionsRepository
from auctions.dependencies import Provide
from auctions.exceptions import ObjectDoesNotExist
from auctions.serializers.push import SubscriptionInfo


class PushService:
    def __init__(
        self,
        push_subscriptions_repository: PushSubscriptionsRepository = Provide(),
        config: Config = Provide(),
    ) -> None:
        self.push_subscriptions_repository = push_subscriptions_repository
        self.config = config

    def send_push(self, push_subscription: PushSubscription, payload: dict[str, ...]) -> None:
        try:
            message = messaging.Message(
                data={key: str(value) for key, value in payload.items()},
                token=push_subscription.token,
            )
            messaging.send(message)
            # webpush(
            #     json.loads(subscription_info.data),
            #     json.dumps(payload),
            #     vapid_private_key=private_key_file.read(),
            #     vapid_claims={"sub": self.config.vapid_sub},
            # )
        except FirebaseError as exception:
            print_exception(exception)

            # if exception.response.status_code in {403, 410}:
            #     self.push_subscriptions_repository.delete([push_subscription])

    def send_event(self, recipient: User | None, event_type: PushEventType, payload: dict[str, ...]):
        if recipient is None:
            subscriptions = self.push_subscriptions_repository.get_many()
        else:
            subscriptions = recipient.subscriptions

        for subscription in subscriptions:
            self.send_push(subscription, {"type": event_type, **payload})

    def subscribe(self, user: User, subscription_info: SubscriptionInfo) -> None:
        try:
            self.push_subscriptions_repository.get_one(PushSubscription.token == subscription_info.token)
        except ObjectDoesNotExist:
            self.push_subscriptions_repository.create(user_id=user.id, token=subscription_info.token)
