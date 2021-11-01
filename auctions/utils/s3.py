import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from urllib.parse import urljoin

import boto3
import boto3.exceptions

from auctions import config


class S3ImageUploader:
    throws = (boto3.exceptions.S3UploadFailedError, boto3.exceptions.S3TransferFailedError)

    def __init__(
        self,
        aws_access_key_id: str = config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key: str = config.AWS_SECRET_ACCESS_KEY,
        aws_storage_bucket_name: str = config.AWS_STORAGE_BUCKET_NAME,
        aws_default_acl: str = config.AWS_DEFAULT_ACL,
        aws_s3_region_name: str = config.AWS_S3_REGION_NAME,
    ):
        self.aws_resource_name = 's3'
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_storage_bucket_name = aws_storage_bucket_name
        self.aws_default_acl = aws_default_acl
        self.aws_s3_region_name = aws_s3_region_name

        self.session = boto3.Session()
        self.s3_resource = self.session.resource(
            service_name='s3',
            region_name=self.aws_s3_region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def get_image_url(self, key: str) -> str:
        return urljoin(
            f'https://{self.aws_storage_bucket_name}.{self.aws_resource_name}.{self.aws_s3_region_name}.'
            f'amazonaws.com',
            key,
        )

    async def upload_image(
        self,
        file_path: str,
        object_name: str,
        bucket_name: Optional[str] = None,
        extra_args: Optional[dict] = None,
    ):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            ThreadPoolExecutor(3),
            self._upload_image,
            file_path,
            object_name,
            bucket_name,
            extra_args,
        )

    def _upload_image(
        self,
        file_path: str,
        object_name: str,
        bucket_name: Optional[str],
        extra_args: Optional[dict],
    ) -> dict:
        if bucket_name is None:
            bucket_name = self.aws_storage_bucket_name

        s3_bucket = self.s3_resource.Bucket(bucket_name)

        if extra_args is None:
            extra_args = {}

        if 'ACL' not in extra_args:
            extra_args['ACL'] = self.aws_default_acl

        s3_bucket.upload_file(
            file_path,
            object_name,
            ExtraArgs=extra_args,
        )

        return {object_name: 'Uploaded'}

    async def delete_image(
        self,
        key: str,
        bucket_name: Optional[str] = None,
    ):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            ThreadPoolExecutor(3),
            self._delete_image,
            key,
            bucket_name,
        )

    def _delete_image(self, key: str, bucket_name: Optional[str]):
        if bucket_name is None:
            bucket_name = self.aws_storage_bucket_name

        self.s3_resource.Object(bucket_name, key).delete()

        return {key: 'Deleted'}
