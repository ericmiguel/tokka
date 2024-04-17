"""
A thin layer between Pydantic and MongoDB/Motor Async.

Tokka is a MongoDB/Motor Async wrapper for Pydantic models.

As a heavy Pydantic/ FastAPI user, I faced myself writing some recurrent
boilerplate code to make things work and remain pleasantly readable when on projects
involving MongoDB.

Nowadays, Pydantic-core is written in Rust, and it's blazing fast. So, Tokka abuses
from Pydantic's model_dump method to serialize Pydantic models into
Dict/MongoDB documents.

No magic, no complex things, only dump. I tried to keep the code as simple as possible
and to not fall deep into Pydantic's internals. I also tried to keep the code as close
as possible to Pymongo's API, so it's familiar to understand and use. But I took some
liberties to make things more Pythonic adding some syntactic sugar here and there, as
well as some extra agnostic functionalities. In addition, Pymongo methods has some
pretty strange kwargs documentation and a not-so-good type annotations, then I worked
on trying make it a little bit friendly.

Personally, I see Tokka as an ingenuous package for lazy people like me.
If you can make some use of it or it make you write less code, I'll be glad.
"""

from typing import Any
from typing import Awaitable
from typing import Literal
from typing import Unpack

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.cursor import Cursor
from pymongo.results import DeleteResult
from pymongo.results import InsertOneResult
from pymongo.results import UpdateResult

from tokka.kwargs import FindKwargs
from tokka.kwargs import ModelDumpKwargs


# TODO: 'Intersection' PEP is under development
#        it will possible be the best and most accurate to type Pydantic`s model_dump
#        and Pymongo's Kwargs.
#
# ? Related issues:
#        https://github.com/python/typing/issues/213
#        https://github.com/python/typing/issues/1445


class Collection:
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    @staticmethod
    def _pop_model_dump_kwargs(
        kwargs: dict[str, Any],
    ) -> tuple[dict[str, Any], ModelDumpKwargs]:
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
        """
        Create a query filter based on the model attributes.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        by : None | str | list[str], optional
            The attribute(s) to filter the query by, by default None.
            Case None, the filter will use all the model attributes.
            Case str, the filter will use only the specified attribute.
            Case list, the filter will use all the specified attributes.

        Returns
        -------
        dict[str, Any]
            Filter mapping attribute names to their values.
        """
        match by:
            case x if isinstance(x, str):
                _filter = {x: getattr(model, x)}
            case xx if isinstance(xx, list):
                _filter = {x: getattr(model, x) for x in xx}
            case _:
                _filter = model.model_dump()

        return _filter

    @staticmethod
    def _make_projection(exclude_keys: set[str]) -> dict[str, Literal[0]]:
        """
        Create a projection to exclude keys from the query result.

        Parameters
        ----------
        exclude_keys : set[str]
            The keys to exclude from the query result.

        Returns
        -------
        dict[str, Literal[0]]
            Projection mapping attribute names to 0. MongoDB uses 0 to exclude.
        """
        return {key: 0 for key in exclude_keys}

    def find_one(
        self,
        model: BaseModel,
        *,
        hide: set[str] = set("_id"),
        filter_by: None | str | list[str] = None,
        **kwargs: Unpack[FindKwargs],
    ) -> Awaitable[Cursor] | Awaitable[None]:
        """
        MongoDB find_one method.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        hide : set[str], optional
            Output fields to hide from the query result (MongoDB projection)
            , by default set("_id")
        filter_by : None | str | list[str], optional
            Model keys to use as query filter, by default None.

        Returns
        -------
        Awaitable[Cursor] | Awaitable[None]
            MongoDB cursor with the query result, or None case any document was
            found.
        """
        _filter = self._make_filter(model, filter_by)
        _projection = self._make_projection(hide)
        kwargs.pop("projection", None)
        return self.collection.find_one(_filter, _projection, **kwargs)

    def find_one_and_replace(
        self,
        model: BaseModel,
        replacement: BaseModel,
        *,
        upsert: bool = False,
        return_old: bool = False,
        filter_by: None | str | list[str] = None,
        hide: set[str] = set("_id"),
        **kwargs: Any,
    ) -> Awaitable[ReturnDocument]:
        """
        MongoDB find_one_and_replace method.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        replacement : BaseModel
            Pydantic model instance to replace the found document.
        upsert : bool, optional
            If True, creates a new document if no document is found, by default False.
        return_old : bool, optional
            If True, returns the old (replaced) document, by default False.
        filter_by : None | str | list[str], optional
            Model keys to use as query filter, by default None.
        hide : set[str], optional
            Output fields to hide from the query result (MongoDB projection),
            by default set("_id")

        Returns
        -------
        Awaitable[ReturnDocument]
            The old (replaced) or new (replacer) document, depending on the
            return_old parameter.
        """
        _filter = self._make_filter(model, filter_by)
        pymongo_kwargs, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)
        pymongo_kwargs.pop("projection", None)
        pymongo_kwargs.pop("filter", None)
        pymongo_kwargs.pop("replacement", None)
        pymongo_kwargs.pop("upsert", None)
        pymongo_kwargs.pop("return_document", None)

        # ? see pymongo.collection.ReturnDocument.BEFORE
        # ? at https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#
        # pymongo.collection.ReturnDocument = False returns the old document
        # pymongo.collection.ReturnDocument = True returns the new document
        # Therefore, we need to invert the return_old value to obtain a more
        # intuitive behavior
        return_old = not return_old

        pymongo_kwargs.pop("return_document", None)

        _replacement = replacement.model_dump(**model_dump_kwargs)
        _projection = self._make_projection(hide)
        return self.collection.find_one_and_replace(
            _filter,
            _replacement,
            _projection,
            upsert=upsert,
            return_document=return_old,
            **pymongo_kwargs,
        )

    def find_one_and_delete(
        self,
        model: BaseModel,
        *,
        filter_by: None | str | list[str] = None,
        hide: set[str] = set("_id"),
        **kwargs: Any,
    ) -> Awaitable[dict[str, Any]]:
        """
        MongoDB find_one_and_delete method.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        filter_by : None | str | list[str], optional
            Model keys to use as query filter, by default None.
        hide : set[str], optional
            Output fields to hide from the query result (MongoDB projection),
            by default set("_id")

        Returns
        -------
        Awaitable[dict[str, Any]]
            The deleted document.
        """
        _filter = self._make_filter(model, filter_by)
        _projection = self._make_projection(hide)
        return self.collection.find_one_and_delete(_filter, _projection, **kwargs)

    def find_one_and_update(
        self,
        model: BaseModel,
        update: dict[str, Any],
        *,
        upsert: bool = False,
        return_old: bool = False,
        filter_by: None | str | list[str] = None,
        hide: set[str] = set("_id"),
        **kwargs: Any,
    ) -> Awaitable[ReturnDocument]:
        """
        MongoDB find_one_and_update method.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        update : dict[str, Any]
            The update to apply over the found document.
        upsert : bool, optional
            If True, creates a new document if no document is found, by default False.
        return_old : bool, optional
            If True, returns the old (replaced) document, by default False.
        filter_by : None | str | list[str], optional
            Model keys to use as query filter, by default None.
        hide : set[str], optional
            Output fields to hide from the query result (MongoDB projection),
            by default set("_id")

        Returns
        -------
        Awaitable[ReturnDocument]
            The old (replaced) or new (updated) document, depending on the
            return_old parameter.
        """
        _filter = self._make_filter(model, filter_by)
        kwargs.pop("projection", None)
        kwargs.pop("filter", None)
        kwargs.pop("replacement", None)
        kwargs.pop("upsert", None)
        kwargs.pop("return_document", None)

        # NOTE: see find_one_and_replace method for more details
        return_old = not return_old

        kwargs.pop("return_document", None)

        _projection = self._make_projection(hide)
        return self.collection.find_one_and_update(
            _filter,
            update,
            _projection,
            upsert=upsert,
            return_document=return_old,
            **kwargs,
        )

    def find_one_and_set(
        self,
        model: BaseModel,
        *,
        upsert: bool = False,
        return_old: bool = False,
        filter_by: None | str | list[str] = None,
        hide: set[str] = set("_id"),
        **kwargs: Any,
    ) -> Awaitable[ReturnDocument]:
        """
        MongoDB find_one_and_update method with $set operator by default.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        upsert : bool, optional
            If True, creates a new document if no document is found, by default False.
        return_old : bool, optional
            If True, returns the old (replaced) document, by default False.
        filter_by : None | str | list[str], optional
            Model keys to use as query filter, by default None.
        hide : set[str], optional
            Output fields to hide from the query result (MongoDB projection),
            by default set("_id")

        Returns
        -------
        Awaitable[ReturnDocument]
            The old (replaced) or new (updated) document, depending on the
            return_old parameter.
        """
        _, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)
        _update = {"$set": model.model_dump(**model_dump_kwargs)}
        return self.find_one_and_update(
            model,
            _update,
            upsert=upsert,
            return_old=return_old,
            filter_by=filter_by,
            hide=hide,
            **kwargs,
        )

    def insert_one(self, model: BaseModel, **kwargs: Any) -> Awaitable[InsertOneResult]:
        """
        MongoDB insert_one method.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.

        Returns
        -------
        Awaitable[InsertOneResult]
            Some MongoDB internal infos about the query result.
        """
        insert_one_kwargs, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)
        document = model.model_dump(**model_dump_kwargs)
        return self.collection.insert_one(document, **insert_one_kwargs)

    def replace_one(
        self,
        model: BaseModel,
        replacement: BaseModel,
        *,
        upsert: bool = False,
        return_old: bool = False,
        filter_by: None | str | list[str] = None,
        **kwargs: Any,
    ) -> Awaitable[UpdateResult]:
        """
        MongoDB replace_one method.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        replacement : BaseModel
            Pydantic model instance to replace the found document.
        upsert : bool, optional
            If True, creates a new document if no document is found, by default False.
        return_old : bool, optional
            If True, returns the old  (replaced) document, by default False.
        filter_by : None | str | list[str], optional
            Model keys to use as query filter, by default None.

        Returns
        -------
        Awaitable[UpdateResult]
            Some MongoDB internal infos about the query result.
        """
        _filter = self._make_filter(model, filter_by)
        pymongo_kwargs, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)
        pymongo_kwargs.pop("projection", None)
        pymongo_kwargs.pop("filter", None)
        pymongo_kwargs.pop("replacement", None)
        pymongo_kwargs.pop("upsert", None)
        pymongo_kwargs.pop("return_document", None)

        # ? see pymongo.collection.ReturnDocument.BEFORE
        # ? at https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#
        # pymongo.collection.ReturnDocument = False returns the old document
        # pymongo.collection.ReturnDocument = True returns the new document
        # Therefore, we need to invert the return_old value to obtain a more
        # intuitive behavior
        return_old = not return_old

        pymongo_kwargs.pop("return_document", None)

        _replacement = replacement.model_dump(**model_dump_kwargs)

        return self.collection.replace_one(
            _filter, _replacement, upsert=upsert, **pymongo_kwargs
        )

    def update_one(
        self,
        model: BaseModel,
        update: dict[str, Any] | BaseModel,
        *,
        filter_by: None | str | list[str] = None,
        upsert: bool = False,
        **kwargs: dict[str, Any],
    ) -> Awaitable[UpdateResult]:
        """
        MongoDB update_one method.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        update: dict[str, Any] | BaseModel
            The update to apply over the found document.
        filter_by : None | str | list[str], optional
            Model keys to use as query filter, by default None.
        upsert : bool, optional
            If True, creates a new document if no document is found, by default False.

        Returns
        -------
        Awaitable[UpdateResult]
            Some MongoDB internal infos about the query result.
        """
        update_one_kwargs, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)

        match update:
            case x if isinstance(x, dict):
                update_value = x
            case xx if isinstance(xx, BaseModel):
                update_value = xx.model_dump(**model_dump_kwargs)
            case _:
                raise ValueError("Update must be a dict or a Pydantic model instance.")

        _update = {"$set": update_value}

        _filter = self._make_filter(model, filter_by)
        return self.collection.update_one(
            _filter, _update, upsert=upsert, **update_one_kwargs
        )

    def set(
        self,
        model: BaseModel,
        update: dict[str, Any] | BaseModel,
        *,
        match: None | str | list[str],
        upsert: bool = False,
        **kwargs: Any,
    ) -> Awaitable[UpdateResult]:
        """
        Update a document using the $set operator.

        Parameters
        ----------
        model : BaseModel
            Pydantic model instance.
        update: dict[str, Any] | BaseModel
            The update to apply over the found document.
        match : None | str | list[str]
            The attribute(s) to filter the query by.
        upsert : bool, optional
            If True, creates a new document if no document is found, by default False.

        Returns
        -------
        Awaitable[UpdateResult]
            Some MongoDB internal infos about the query result.
        """
        update_one_kwargs, model_dump_kwargs = self._pop_model_dump_kwargs(kwargs)
        _filter = self._make_filter(model, match)
        
        match update:
            case x if isinstance(x, dict):
                update_value = x
            case xx if isinstance(xx, BaseModel):
                update_value = xx.model_dump(**model_dump_kwargs)
            case _:
                raise ValueError("Update must be a dict or a Pydantic model instance.")

        _update = {"$set": update_value}
        return self.collection.update_one(_filter, _update, upsert, **update_one_kwargs)

    def delete_one(self) -> Awaitable[DeleteResult]:
        raise NotImplementedError


class Database:
    """A MongoDB/Motor Async database wrapper, as convenience."""

    def __init__(self, name: str, *, connection: str | AsyncIOMotorClient) -> None:
        """
        Database init.

        Parameters
        ----------
        name : str
            MongoDB database name.
        connection : str | AsyncIOMotorClient
            MongoDB connection URI or AsyncIOMotorClient instance.
        """
        match connection:
            case str():
                self.client = AsyncIOMotorClient(connection)
            case AsyncIOMotorClient():
                self.client = connection

        self._connection = self.client.get_database(name)

    def get_collection(self, name: str) -> Collection:
        """Get a MongoDB (Tokka wrapped) collection."""
        return Collection(self._connection.get_collection(name))

    def close(self) -> None:
        """Close the MongoDB connection."""
        self.client.close()


class Client:
    """A MongoDB/Motor Async client wrapper, as convenience."""

    def __init__(self, uri: str, **kwargs: Any) -> None:
        """Client init. Connects to the MongoDB server using the URI."""
        self.client = AsyncIOMotorClient(uri, **kwargs)

    def get_database(self, name: str) -> Database:
        """Get a MongoDB (Tokka wrapped) database by name."""
        return Database(name, connection=self.client)

    def close(self) -> None:
        """Close the MongoDB connection."""
        self.client.close()
