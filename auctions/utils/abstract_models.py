import asyncio
from datetime import datetime

from pydantic import BaseModel
from tortoise import fields, Model


class CreatedRecordedModel(Model):
    created = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True


class CreatedUpdatedRecordedModel(CreatedRecordedModel):
    updated = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class PyCreatedRecordedModel(BaseModel):
    created: datetime


class PyCreatedUpdatedRecordedModel(PyCreatedRecordedModel):
    updated: datetime


class PyRelatedOne():
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: fields.ReverseRelation):
        if not isinstance(value, fields.ReverseRelation):
            raise TypeError('tortoise.fields.relational.ReverseRelation required')

        return asyncio.get_running_loop().run_until_complete(value.all())


class PyRelatedMany(list):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: fields.ReverseRelation):
        if not isinstance(value, fields.ReverseRelation):
            raise TypeError('tortoise.fields.relational.ReverseRelation required')

        return asyncio.get_running_loop().run_until_complete(value.all())
