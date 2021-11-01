from typing import Optional

from pydantic import BaseModel, Json


class Job(BaseModel):
    job_id: str
    function_name: str
    args: Json
    kwargs: Json
    success: bool
    result: Json


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    avatar: str


class Group(BaseModel):
    id: int
    group_id: int
    name: Optional[str]
    cover: Optional[str]


class Album(BaseModel):
    id: int
    album_id: int
    group: Group
    title: str
    description: Optional[str]
    upload_url: Optional[str]
