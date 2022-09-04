import random
from pathlib import Path
from typing import Any
from typing import Optional

import requests
from vk.session import API

from auctions.config import Config
from auctions.db.models.enum import ExternalTokenType
from auctions.db.models.enum import VKIntentType
from auctions.db.repositories.external import ExternalTokensRepository
from auctions.utils.use_token import use_token


class VKRequestService:
    def __init__(self, external_tokens_repository: ExternalTokensRepository, config: Config) -> None:
        self.external_tokens_repository = external_tokens_repository
        self.config = config

    @use_token(ExternalTokenType.VK_GROUP)
    def get_callback_confirmation_code(self, group_id: int, *, token_type: ExternalTokenType) -> str:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)
        self.external_tokens_repository.wait_unblock(token)
        result = API(access_token=token.token, v=self.config.vk["v"]).groups.getCallbackConfirmationCode(
            group_id=group_id,
        )
        return result["code"]

    @use_token(ExternalTokenType.VK_USER)
    def create_album(
        self,
        group_id: int,
        title: str,
        description: Optional[str] = None,
        *,
        token_type: ExternalTokenType,
    ) -> tuple[int, str]:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)

        params = {
            "group_id": group_id,
            "title": title,
            "upload_by_admins_only": 1,
        }

        if description is not None:
            params["description"] = description

        self.external_tokens_repository.wait_unblock(token)
        result = API(
            access_token=token.token,
            v=self.config.vk["v"],
        ).photos.createAlbum(**params)

        album_id = result["id"]

        self.external_tokens_repository.wait_unblock(token)
        result = API(access_token=token.token, v=self.config.vk["v"]).photos.getUploadServer(
            group_id=group_id,
            album_id=album_id,
        )
        return album_id, result["upload_url"]

    @use_token(ExternalTokenType.VK_USER)
    def upload_photo(
        self,
        group_id: int,
        album_id: int,
        upload_url: str,
        photo_path: Path,
        description: Optional[str] = None,
        *,
        token_type: ExternalTokenType,
    ) -> int:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)

        with photo_path.open("rb") as file:
            result = requests.post(upload_url, files={"file1": file})

        result = result.json()
        params = {
            "server": result["server"],
            "photos_list": result["photos_list"],
            "hash": result["hash"],
            "group_id": group_id,
            "album_id": album_id,
        }

        if description is not None:
            params["caption"] = description

        self.external_tokens_repository.wait_unblock(token)
        result = API(access_token=token.token, v=self.config.vk["v"]).photos.save(**params)

        return result[0]["id"]

    @use_token(ExternalTokenType.VK_USER)
    def send_comment(
        self,
        group_id: int,
        photo_id: int,
        message: str,
        attachments: str,
        reply_to: int,
        *,
        token_type: ExternalTokenType,
    ) -> None:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)
        self.external_tokens_repository.wait_unblock(token)
        API(access_token=token.token, v=self.config.vk["v"]).photos.createComment(
            owner_id=-group_id,
            photo_id=photo_id,
            message=message,
            attachments=attachments,
            from_group=1,
            reply_to_comment=reply_to,
        )

    @use_token(ExternalTokenType.VK_USER)
    def delete_comment(
        self,
        group_id: int,
        comment_id: str,
        *,
        token_type: ExternalTokenType,
    ) -> None:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)
        self.external_tokens_repository.wait_unblock(token)
        API(access_token=token.token, v=self.config.vk["v"]).photos.deleteComment(
            owner_id=-group_id,
            comment_id=comment_id,
        )

    @use_token(ExternalTokenType.VK_GROUP)
    def send_message(
        self,
        group_id: int,
        user_id: int,
        message: str,
        attachments: Optional[str] = None,
        keyboard: Optional[dict[str, Any]] = None,
        intent: str = "confirmed_notification",
        *,
        token_type: ExternalTokenType,
    ) -> None:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)

        params = {
            "user_id": user_id,
            "peer_id": user_id,
            "message": message,
            "intent": intent,
            "random_id": random.randint(0, 100000),
        }

        if attachments is not None:
            params["attachments"] = attachments

        if keyboard is not None:
            params["keyboard"] = keyboard

        self.external_tokens_repository.wait_unblock(token)
        API(access_token=token.token, v=self.config.vk["v"]).messages.send(**params)

    @use_token(ExternalTokenType.VK_GROUP)
    def get_user(self, group_id: int, user_id: int, *, token_type: ExternalTokenType) -> dict[str, Any]:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)
        self.external_tokens_repository.wait_unblock(token)
        result = API(access_token=token.token, v=self.config.vk["v"]).users.get(user_ids=user_id, fields="photo_50")
        return result[0]

    @use_token(ExternalTokenType.VK_GROUP)
    def get_intent_users(self, group_id: int, intent: VKIntentType, *, token_type: ExternalTokenType) -> list[int]:
        token = self.external_tokens_repository.get_token(str(group_id), token_type)

        user_ids = []
        page_size = 200
        page = 0

        while True:
            self.external_tokens_repository.wait_unblock(token)
            result = API(access_token=token.token, v=self.config.vk["v"]).messages.getIntentUsers(
                intent=intent.value,
                subscribe_id=self.config.vk["subscribe_id"],
                count=page_size,
                offset=page * page_size,
            )

            user_ids.extend(result["items"])
            if len(result["items"]) < page_size:
                break

            page += 1

        return user_ids
