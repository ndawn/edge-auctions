import asyncio
from datetime import datetime
import json
from typing import Any, Optional
from urllib.parse import urljoin

from aiohttp import ClientResponse, ClientSession
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from auctions.ams.models import Album, Job, User
from auctions.config import AMS_TOKEN, AMS_URL


class AlbumCreate(BaseModel):
    response: dict
    album: Album


class AmsApiService:
    @staticmethod
    async def _validate_response(response: ClientResponse):
        if not (200 <= response.status < 400):
            try:
                detail = (await response.json())['detail']
            except (json.JSONDecodeError, KeyError):
                detail = f'Status code: {response.status}'
            except:
                print(await response.text())
                raise

            raise HTTPException(status_code=response.status, detail=f'Error while requesting AMS service: {detail}')

    @staticmethod
    async def _unwrap_response(response: ClientResponse) -> Any:
        if response.headers.get('Content-Type', '') == 'application/json':
            return await response.json()

        return await response.text()

    @staticmethod
    async def _request(method: str, uri: str, data: Optional[dict] = None, await_job: bool = True) -> Any:
        print(f'Attempting to make a request to {urljoin(AMS_URL, uri)}')
        async with ClientSession() as session:
            async with session.request(
                method=method,
                url=urljoin(AMS_URL, uri),
                json=data,
                headers={'Authorization': f'Bearer {AMS_TOKEN}'},
            ) as response:
                print(f'Received raw response: {await response.text()}')
                await AmsApiService._validate_response(response)
                result = await AmsApiService._unwrap_response(response)

        if not await_job:
            return result

        job_id = result.get('job_id')

        if job_id is None:
            raise ValueError('Job ID must present in the response in order to await for a job to finish')

        retry_counter = 1
        retry_elapsed = 0
        retry_max = 60

        while retry_elapsed <= retry_max:
            await asyncio.sleep(retry_counter)
            retry_elapsed += retry_counter
            retry_counter *= 2
            job = await AmsApiService.get_job(job_id)
            if job.finished_at is not None and job.success:
                return job.result

        return None

    @staticmethod
    async def get_job(job_id: str) -> Job:
        return Job(**(await AmsApiService._request('GET', f'/jobs/{job_id}', await_job=False)))

    @staticmethod
    async def get_user(user_id: int) -> Optional[User]:
        try:
            return User.parse_obj(await AmsApiService._request('GET', f'/vk/users/{user_id}', await_job=False))
        except HTTPException as exc:
            if exc.status_code == HTTP_404_NOT_FOUND:
                return None
            raise

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

        return await AmsApiService._request('POST', '/vk/comments', params)

    @staticmethod
    async def delete_comment(
        group_id: int,
        comment_id: int,
    ) -> str:
        params = {
            'group_id': group_id,
            'comment_id': comment_id,
        }

        return await AmsApiService._request('DELETE', '/vk/comments', params)

    @staticmethod
    async def send_message(
        group_id: int,
        user_id: int,
        text: str,
    ) -> Any:
        return await AmsApiService._request('POST', '/vk/messages', {
            'group_id': group_id,
            'user_id': user_id,
            'text': text,
        })

    @staticmethod
    async def broadcast_notification(text: str) -> Any:
        return await AmsApiService._request('POST', '/tg/broadcast', {'text': text})

    @staticmethod
    async def schedule_auction_close(auction_uuid: str, run_at: datetime) -> Any:
        return await AmsApiService._request(
            'POST',
            '/auctions/schedule_close/auction',
            {
                'auction_uuid': auction_uuid,
                'run_at': int(run_at.timestamp()),
            },
            await_job=False,
        )

    @staticmethod
    async def schedule_auction_set_close(set_uuid: str, run_at: datetime) -> Any:
        return await AmsApiService._request(
            'POST',
            '/auctions/schedule_close/set',
            {
                'set_uuid': set_uuid,
                'run_at': int(run_at.timestamp()),
            },
            await_job=False,
        )

    @staticmethod
    async def list_albums() -> list[Album]:
        return [Album(**album) for album in await AmsApiService._request('GET', '/vk/albums', await_job=False)]

    @staticmethod
    async def get_album(album_id: int) -> Album:
        return Album(**(await AmsApiService._request('GET', f'/vk/albums/{album_id}', await_job=False)))

    @staticmethod
    async def create_album(group_id: int, title: str, description: Optional[str] = None) -> AlbumCreate:
        params = {
            'group_id': group_id,
            'title': title,
        }

        if description is not None:
            params['description'] = description

        response = await AmsApiService._request('POST', '/vk/albums', params)

        album_id = response.get('album_id')
        if album_id is None:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail='An error occurred while creating an album',
            )

        album = await AmsApiService.get_album(album_id)
        return AlbumCreate(response=response, album=album)

    @staticmethod
    async def update_album(
        album_id: int,
        title: Optional[str] = ...,
        description: Optional[str] = ...,
        external: bool = True,
    ) -> Any:
        params = {'external': external}

        if title is not ...:
            params['title'] = title

        if description is not ...:
            params['description'] = description

        return await AmsApiService._request('PUT', f'/vk/albums/{album_id}', params)

    @staticmethod
    async def delete_album(album_id: int) -> str:
        return await AmsApiService._request('DELETE', f'/vk/albums/{album_id}')

    @staticmethod
    async def upload_to_album(album_id: int, url: str, description: str, auction_uuid: str) -> Any:
        return await AmsApiService._request(
            'POST',
            f'/vk/albums/{album_id}/upload',
            {'url': url, 'description': description, 'auction_uuid': auction_uuid},
        )

    @staticmethod
    async def upload_batch_to_album(album_id: int, batch: list[dict[str, str]]) -> str:
        return await AmsApiService._request('POST', f'/vk/albums/{album_id}/upload_batch', {'batch': batch})
