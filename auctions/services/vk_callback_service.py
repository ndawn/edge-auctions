from flask import Response
from sqlalchemy.orm.attributes import flag_modified

from auctions.config import Config
from auctions.db.models.auction_targets import AuctionTarget
from auctions.db.models.auctions import Auction
from auctions.db.models.bidders import Bidder
from auctions.db.models.enum import CreateBidFailReason
from auctions.db.models.enum import ExternalSource
from auctions.db.models.enum import VKCallbackEventType
from auctions.db.models.enum import VKCallbackMessageEventCommandType
from auctions.db.models.enum import VKCallbackMessageEventPayloadActionType
from auctions.db.models.enum import VKIntentType
from auctions.db.models.external import ExternalEntity
from auctions.db.repositories.auction_targets import AuctionTargetsRepository
from auctions.db.repositories.auctions import AuctionsRepository
from auctions.db.repositories.bidders import BiddersRepository
from auctions.db.repositories.external import ExternalEntitiesRepository
from auctions.db.repositories.external import ExternalTokensRepository
from auctions.exceptions import CreateBidFailed
from auctions.exceptions import ObjectDoesNotExist
from auctions.services.auctions_service import AuctionsService
from auctions.services.vk_notification_service import VKNotificationService
from auctions.services.vk_request_service import VKRequestService
from auctions.utils import text_constants


class VKCallbackService:
    def __init__(
        self,
        auctions_service: AuctionsService,
        vk_notification_service: VKNotificationService,
        vk_request_service: VKRequestService,
        auction_targets_repository: AuctionTargetsRepository,
        auctions_repository: AuctionsRepository,
        bidders_repository: BiddersRepository,
        external_entities_repository: ExternalEntitiesRepository,
        external_tokens_repository: ExternalTokensRepository,
        config: Config,
    ) -> None:
        self.auctions_service = auctions_service
        self.vk_notification_service = vk_notification_service
        self.vk_request_service = vk_request_service
        self.auction_targets_repository = auction_targets_repository
        self.auctions_repository = auctions_repository
        self.bidders_repository = bidders_repository
        self.external_entities_repository = external_entities_repository
        self.external_tokens_repository = external_tokens_repository
        self.config = config

    def handle_callback_message(self, args: dict[str, ...]) -> Response:
        if args["type"] == VKCallbackEventType.SERVER_CONFIRMATION:
            return Response(self.get_callback_confirmation_code(args))

        if args["type"] == VKCallbackEventType.MESSAGE_EVENT:
            self.process_message_event(args)
        elif args["type"] == VKCallbackEventType.MESSAGE_NEW:
            self.process_message(args)
        elif args["type"] in (
            VKCallbackEventType.PHOTO_COMMENT_NEW,
            VKCallbackEventType.PHOTO_COMMENT_EDIT,
            VKCallbackEventType.PHOTO_COMMENT_DELETE,
            VKCallbackEventType.PHOTO_COMMENT_RESTORE,
        ):
            self.process_photo_comment(args)

        return Response('ok')

    def get_callback_confirmation_code(self, args: dict[str, ...]) -> str:
        return self.vk_request_service.get_callback_confirmation_code(args["group_id"])

    def process_message_event(self, args: dict[str, ...]) -> None:
        event = args["object"]

        command = event.get("payload", {}).get("command")
        action = event.get("payload", {}).get("action", {}).get("type")

        if command != VKCallbackMessageEventCommandType.INTERNAL_COMMAND.value:
            return

        if action == VKCallbackMessageEventPayloadActionType.INTENT_SUBSCRIBE.value:
            self.process_intent_subscribe(args)
        elif action == VKCallbackMessageEventPayloadActionType.INTENT_UNSUBSCRIBE.value:
            self.process_intent_unsubscribe(args)

    def process_message(self, args: dict[str, ...]) -> None:
        message = args.get("message", {})
        message_text = message.get("text", "").lower().strip()

        if (
            message_text
            in (
                text_constants.INTENT_SUBSCRIBE_REQUEST.lower(),
                text_constants.INTENT_UNSUBSCRIBE_REQUEST.lower(),
            )
            and message.get("payload") is not None
        ):
            self.process_message_event(
                {
                    "group_id": args["group_id"],
                    "user_id": message.get("from_id"),
                    "peer_id": message.get("from_id"),
                    "payload": message.get("payload"),
                }
            )
            return

        if message == text_constants.INTENT_SUBSCRIBE_REQUEST_COLD.lower():
            text = text_constants.INTENT_SUBSCRIBE_CALL
            button_action_type = VKCallbackMessageEventPayloadActionType.INTENT_SUBSCRIBE.value
            button_label = text_constants.INTENT_SUBSCRIBE_REQUEST
        elif message == text_constants.INTENT_UNSUBSCRIBE_REQUEST_COLD.lower():
            text = text_constants.INTENT_UNSUBSCRIBE_CALL
            button_action_type = VKCallbackMessageEventPayloadActionType.INTENT_UNSUBSCRIBE.value
            button_label = text_constants.INTENT_UNSUBSCRIBE_REQUEST
        else:
            return

        self.vk_request_service.send_message(
            group_id=args["group_id"],
            user_id=message.get("from_id"),
            message=text,
            keyboard={
                "one_time": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": button_action_type,
                                "label": button_label,
                                "peer_id": message.get("from_id"),
                                "intent": VKIntentType.CONFIRMED_NOTIFICATION.value,
                                "subscribe_id": self.config.vk_subscribe_id,
                            },
                        }
                    ]
                ],
            },
        )

    def process_photo_comment(self, args: dict[str, ...]) -> None:
        comment = args["object"]
        group_id = args["group_id"]
        photo_id = comment.get("photo_id")
        comment_id = comment.get("id")
        from_id = comment.get("from_id")
        comment_text = comment.get("text", "").strip().capitalize()

        if from_id == -group_id:
            return

        try:
            auction = self.auctions_repository.get_one(Auction.external.any(entity_id=str(photo_id)))
        except ObjectDoesNotExist:
            return

        if not comment_text.isnumeric() or comment_text != text_constants.BUYOUT_REQUEST:
            return

        bidder = self._get_or_create_bidder(group_id=group_id, user_id=from_id)
        external_bidder = bidder.get_external(ExternalSource.VK)

        try:
            bid = self.auctions_service.create_bid(auction, bidder, comment_text)
        except CreateBidFailed as exception:
            if exception.reason == CreateBidFailReason.AUCTION_NOT_ACTIVE:
                return

            if exception.reason == CreateBidFailReason.INVALID_BUYOUT:
                message = text_constants.INVALID_BUYOUT
            else:
                message = text_constants.INVALID_BID

            self.vk_request_service.send_message(
                group_id=group_id,
                user_id=from_id,
                message=message,
            )
            return

        external_bid = self.external_entities_repository.create(
            source=ExternalSource.VK,
            entity_id=str(comment_id),
        )
        bid.external = external_bid

        self.vk_notification_service.notify_bid_beaten(bid, bid.auction.get_last_bid())

        if not external_bidder.extra.get("is_subscribed", False):
            self.vk_notification_service.notify_bidder_not_registered(bid)

    def process_intent_subscribe(self, args: dict[str, ...]) -> None:
        event = args["object"]

        try:
            user = self.external_entities_repository.get_one(ExternalEntity.entity_id == str(event["user_id"]))
            external_user = user.get_external(ExternalSource.VK)
        except ObjectDoesNotExist:
            target = self.auction_targets_repository.get_one(
                AuctionTarget.external.any(entity_id=str(args["group_id"]))
            )

            external_user_data = self.vk_request_service.get_user(args["group_id"], event["user_id"])

            user = self.bidders_repository.create(
                target=target,
                first_name=external_user_data["first_name"],
                last_name=external_user_data["last_name"],
                avatar=external_user_data["photo_50"],
            )
            external_user = self.external_entities_repository.create(
                source=ExternalSource.VK,
                entity_id=str(event["user_id"]),
            )

            self.bidders_repository.add_external(user, external_user)

        if external_user.extra.get("is_subscribed", False):
            return self._send_intent_event_answer(args, text_constants.INTENT_SUBSCRIBED_ALREADY)

        external_user.extra["is_subscribed"] = True
        flag_modified(external_user, "extra")
        return self._send_intent_event_answer(args, text_constants.INTENT_SUBSCRIBED)

    def process_intent_unsubscribe(self, args: dict[str, ...]) -> None:
        event = args["object"]

        try:
            user = self.external_entities_repository.get_one(ExternalEntity.entity_id == str(event["user_id"]))
            external_user = user.get_external(ExternalSource.VK)
        except ObjectDoesNotExist:
            return

        if not external_user.extra.get("is_subscribed", False):
            self._send_intent_event_answer(args, text_constants.INTENT_UNSUBSCRIBED_ALREADY)
            return

        external_user.extra["is_subscribed"] = False
        flag_modified(external_user, "extra")
        self._send_intent_event_answer(args, text_constants.INTENT_UNSUBSCRIBED)

    def _send_intent_event_answer(self, args: dict[str, ...], text: str) -> None:
        event = args["object"]

        if text in (
            text_constants.INTENT_SUBSCRIBED,
            text_constants.INTENT_SUBSCRIBED_ALREADY,
        ):
            button_action_type = VKCallbackMessageEventPayloadActionType.INTENT_UNSUBSCRIBE.value
            label = text_constants.INTENT_UNSUBSCRIBE_REQUEST
        else:
            button_action_type = VKCallbackMessageEventPayloadActionType.INTENT_SUBSCRIBE.value
            label = text_constants.INTENT_SUBSCRIBE_REQUEST

        self.vk_request_service.send_message(
            group_id=args["group_id"],
            user_id=event["user_id"],
            message=text,
            keyboard={
                "one_time": True,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": button_action_type,
                                "label": label,
                                "peer_id": event["user_id"],
                                "intent": VKIntentType.CONFIRMED_NOTIFICATION.value,
                                "subscribe_id": self.config.vk_subscribe_id,
                            },
                        }
                    ]
                ],
            },
        )

    def _get_or_create_bidder(self, group_id: int, user_id: int) -> Bidder:
        try:
            return self.external_entities_repository.get_one(ExternalEntity.entity_id == str(user_id))
        except ObjectDoesNotExist:
            pass

        target = self.auction_targets_repository.get_one(
            AuctionTarget.external.any(entity_id=str(group_id))
        )

        external_user_data = self.vk_request_service.get_user(group_id, user_id)

        user = self.bidders_repository.create(
            target=target,
            first_name=external_user_data["first_name"],
            last_name=external_user_data["last_name"],
            avatar=external_user_data["photo_50"],
        )
        external_user = self.external_entities_repository.create(
            source=ExternalSource.VK,
            entity_id=str(user_id),
        )

        self.bidders_repository.add_external(user, external_user)
        return user
