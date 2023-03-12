import json
from dataclasses import asdict
from traceback import print_exception

from pywebpush import webpush
from pywebpush import WebPushException

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

    def get_public_key(self) -> str:
        with open(self.config.vapid_public_key) as public_key_file:
            return public_key_file.read()

    def send_push(self, subscription_info: PushSubscription, payload: ...) -> None:
        try:
            with open(self.config.vapid_private_key) as private_key_file:
                webpush(
                    json.loads(subscription_info.data),
                    json.dumps(payload),
                    vapid_private_key=private_key_file.read(),
                    vapid_claims={"sub": self.config.vapid_sub},
                )
        except WebPushException as exception:
            print_exception(type(exception), exception, exception.__traceback__)

            if exception.response.status_code in {403, 410}:
                self.push_subscriptions_repository.delete([subscription_info])

    def send_event(self, recipient: User | None, event_type: PushEventType, payload: dict[str, ...]):
        if recipient is None:
            subscriptions = self.push_subscriptions_repository.get_many()
        else:
            subscriptions = recipient.subscriptions

        for subscription in subscriptions:
            self.send_push(subscription, {"type": event_type, **payload})

    def subscribe(self, user: User, subscription_info: SubscriptionInfo) -> None:
        try:
            subscription = self.push_subscriptions_repository.get_one(
                PushSubscription.endpoint == subscription_info.endpoint
            )

            subscription.data = json.dumps(asdict(subscription_info))
        except ObjectDoesNotExist:
            self.push_subscriptions_repository.create(
                user=user,
                endpoint=subscription_info.endpoint,
                data=json.dumps(asdict(subscription_info)),
            )
