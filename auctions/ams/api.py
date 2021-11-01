import json
from typing import Any, Optional
from urllib.parse import urljoin

from aiohttp import ClientResponse, ClientSession
from fastapi.exceptions import HTTPException

from auctions.ams.models import Album, Job, User
from auctions.config import AMS_URL


def build_url(uri: str) -> str:
    return urljoin(AMS_URL, uri)


class AmsApiService:
    session = ClientSession()

    @staticmethod
    async def _validate_response(response: ClientResponse):
        if not (200 <= response.status < 400):
            try:
                detail = ': ' + (await response.json())['detail']
            except (json.JSONDecodeError, KeyError):
                detail = ''

            raise HTTPException(status_code=response.status, detail='Error while requesting AMS service' + detail)

    @staticmethod
    async def _unwrap_response(response: ClientResponse) -> Any:
        if response.headers.get('Content-Type', '') == 'application/json':
            return await response.json()

        return await response.text()

    @staticmethod
    async def _request(method: str, uri: str, data: Optional[dict] = None) -> Any:
        async with AmsApiService.session:
            async with AmsApiService.session.request(
                method=method,
                url=build_url(uri),
                json=data,
            ) as response:
                await AmsApiService._validate_response(response)
                return AmsApiService._unwrap_response(response)

    @staticmethod
    async def get_job(job_id: str) -> Job:
        return Job(**(await AmsApiService._request('GET', f'/jobs/{job_id}')))

    @staticmethod
    async def get_user(user_id: int) -> User:
        return User.parse_obj(await AmsApiService._request('GET', f'/vk/users/{user_id}'))

    @staticmethod
    async def send_comment(
        group_id: int,
        photo_id: int,
        text: str,
        reply_to: Optional[int] = None,
    ) -> str:
        params = {
            'group_id': group_id,
            'photo_id': photo_id,
            'text': text,
        }

        if reply_to is not None:
            params['reply_to'] = reply_to

        return (await AmsApiService._request('POST', '/vk/comments', params))['job_id']

    @staticmethod
    async def send_message(
        group_id: int,
        user_id: int,
        text: str,
    ) -> str:
        return (await AmsApiService._request('POST', '/vk/messages', {
            'group_id': group_id,
            'user_id': user_id,
            'text': text,
        }))['job_id']

    @staticmethod
    async def broadcast_notification(text: str) -> str:
        return (await AmsApiService._request('POST', '/tg/broadcast', {'text': text}))['job_id']

    @staticmethod
    async def schedule_close(auction_id: str, run_at: int) -> str:
        return (await AmsApiService._request('POST', '/auctions/schedule_close', {
            'auction_id': auction_id,
            'run_at': run_at,
        }))['job_id']

    @staticmethod
    async def list_albums() -> list[Album]:
        return [Album(**album) for album in await AmsApiService._request('GET', '/vk/albums')]

    @staticmethod
    async def get_album(album_id: int) -> Album:
        return Album(**(await AmsApiService._request('GET', f'/vk/albums/{album_id}')))

    @staticmethod
    async def create_album(group_id: int, title: str, description: Optional[str] = None) -> str:
        params = {
            'group_id': group_id,
            'title': title,
        }

        if description is not None:
            params['description'] = description

        return (await AmsApiService._request('POST', '/vk/comments', params))['job_id']

    @staticmethod
    async def update_album(
        album_id: int,
        title: Optional[str] = ...,
        description: Optional[str] = ...,
        external: bool = True,
    ) -> str:
        params = {'external': external}

        if title is not ...:
            params['title'] = title

        if description is not ...:
            params['description'] = description

        return (await AmsApiService._request('PUT', f'/vk/albums/{album_id}', params))['job_id']

    @staticmethod
    async def delete_album(album_id: int) -> str:
        return (await AmsApiService._request('DELETE', f'/vk/albums/{album_id}'))['job_id']

    @staticmethod
    async def upload_batch_to_album(album_id: int, batch: list[tuple[str, str]]) -> str:
        return (await AmsApiService._request('POST', f'/vk/albums/{album_id}/upload_batch', {'batch': batch}))['job_id']
