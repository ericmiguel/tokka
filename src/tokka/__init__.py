from typing import Any
from typing import Awaitable
from typing import NoReturn
from typing import Unpack

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.cursor import Cursor
from pymongo.results import DeleteResult
from pymongo.results import InsertOneResult
from pymongo.results import UpdateResult
from tokka.types import FindKwargs
from typing import Literal
from tokka.types import ModelDumpKwargs


class Collection:
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    @staticmethod
    def _pop_model_dump_kwargs(kwargs: dict[str, Any]) -> tuple[dict[str, Any], ModelDumpKwargs]:
        model_dump_kwargs: ModelDumpKwargs = {
            "mode": kwargs.pop("mode", "python"),
            "include": kwargs.pop("include", None),
            "exclude": kwargs.pop("exclude", None),
            "by_alias": kwargs.pop("by_alias", False),
            "exclude_unset": kwargs.pop("exclude_unset", False),
            "exclude_defaults": kwargs.pop("exclude_defaults", False),
            "exclude_none": kwargs.pop("exclude_none", False),
            "round_trip": kwargs.pop("round_trip", False),
            "warnings": kwargs.pop("warnings", True),
        }

        if isinstance(model_dump_kwargs["include"], str):
            model_dump_kwargs["include"] = set([model_dump_kwargs["include"]])

        if isinstance(model_dump_kwargs["exclude"], str):
            model_dump_kwargs["exclude"] = set([model_dump_kwargs["exclude"]])

        return kwargs, model_dump_kwargs

    @staticmethod
    def _make_filter(
        model: BaseModel, by: None | str | list[str] = None
    ) -> dict[str, Any]:
        match by:
            case x if isinstance(x, str):
                filter = {x: getattr(model, x)}
            case xx if isinstance(xx, list):
                filter = {x: getattr(model, x) for x in xx}
            case _:
                filter = model.model_dump()

        return filter

    @staticmethod
    def _make_projection(exclude_keys: set[str]) -> dict[str, Literal[0]]:
        return {key: 0 for key in exclude_keys}

    def find_one(
        self,
        model: BaseModel,
        filter_by: None | str | list[str] = None,
        **kwargs: Unpack[FindKwargs],
    ) -> Awaitable[Cursor] | Awaitable[None]:
        filter = self._make_filter(model, filter_by)
        return self.collection.find_one(filter, kwargs)

    def find_one_and_replace(
        self,
        model: BaseModel,
        replacement: BaseModel,
        *,
        filter_by: None | str | list[str] = None,
        hide: set[str] = set("_id"),
    ) -> Awaitable[ReturnDocument]:
        _filter = self._make_filter(model, filter_by)
        _replacement = replacement.model_dump()
        _projection = self._make_projection(hide)
        return self.collection.find_one_and_replace(_filter, _replacement, _projection)

    def find_one_and_delete(self) -> NoReturn:
        raise NotImplementedError

    def find_one_and_update(
        self,
    ) -> Awaitable[ReturnDocument]:
        raise NotImplementedError

    def insert_one(
        self, model: BaseModel, **kwargs: Any
    ) -> Awaitable[InsertOneResult]:
        insert_one_kwargs, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)
        document = model.model_dump(**model_dump_kwargs)
        return self.collection.insert_one(document, **insert_one_kwargs)

    def replace_one(self) -> NoReturn:
        raise NotImplementedError

    def update_one(
        self,
        model: BaseModel,
        dump_kwargs: None | dict[str, Any] = None,
        *,
        filter_by: None | str | list[str] = None,
        upsert: bool = False,
    ) -> Awaitable[UpdateResult]:
        update = model.model_dump(*dump_kwargs)
        filter = self._make_filter(model, filter_by)
        return self.collection.update_one(filter, update, upsert)

    def set(
        self,
        model: BaseModel,
        *,
        match: None | str | list[str],
        upsert: bool = False,
        **kwargs: Any,
    ) -> Awaitable[UpdateResult]:
        update_one_kwargs, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)
        filter = self._make_filter(model, match)
        update = {"$set": model.model_dump(**model_dump_kwargs)}

        return self.collection.update_one(filter, update, upsert, **update_one_kwargs)

    def delete_one(self) -> Awaitable[DeleteResult]:
        raise NotImplementedError


class Database:
    def __init__(self, name: str, *, connection: str | AsyncIOMotorClient) -> None:
        match connection:
            case str():
                self.client = AsyncIOMotorClient(connection)
            case AsyncIOMotorClient():
                self.client = connection

        self._connection = self.client.get_database(name)

    def get_collection(self, name: str) -> Collection:
        return Collection(self._connection.get_collection(name))

    def close(self) -> None:
        self.client.close()


class Client:
    def __init__(self, uri: str) -> None:
        self.client = AsyncIOMotorClient(uri)

    def get_database(self, name: str) -> Database:
        return Database(name, connection=self.client)

    def close(self) -> None:
        self.client.close()
