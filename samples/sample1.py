"""Tokka sample code."""

import asyncio

import config
from icecream import ic
from pydantic import BaseModel
from tokka import Collection
from tokka import Database


class User(BaseModel):
    """Sample data."""

    name: str
    email: str


class DB(Database):
    """A tokka.Database subclass to easily accesst the your collections."""

    @property
    def users(self) -> Collection:
        return self.get_collection("users")


if __name__ == "__main__":
    db = DB("tokka", connection=config.mongodb.URI)
    user1 = User(name="John Doe", email="john.doe@example.com.br")
    user2 = User(name="Emma Su", email="ema.sue@example.com.br")
    user3 = User(name="Joanne Doe", email="joanne.doe@example.com.br")

    async def crud() -> None:
        """Perform CRUD some sample operations."""
        insert_results = await asyncio.gather(
            db.users.insert_one(user1),
            db.users.insert_one(user2),
            db.users.insert_one(user1, exclude="name"),
        )

        set_results = await asyncio.gather(
            db.users.set(user1, match="name", upsert=True, exclude="email"),
            db.users.find_one(user2, filter_by="name"),
        )

        find_results = await asyncio.gather(
            db.users.find_one(user1, filter_by="name"),
            db.users.find_one(user2, filter_by="name"),
            db.users.find_one(user1, filter_by="email"),
        )

        find_one_and_replace_results = await asyncio.gather(
            db.users.find_one_and_replace(user1, user2, filter_by="name"),
            db.users.find_one_and_replace(
                user2, user1, filter_by="name", return_old=True
            ),
        )

        find_one_and_update_results = await asyncio.gather(
            db.users.find_one_and_update(
                user1, {"$set": {"name": "Mario"}}, filter_by="name", return_old=False
            ),
            db.users.find_one_and_update(
                user2, {"$set": {"name": "Maria"}}, filter_by="name", return_old=True
            ),
        )

        user1.name = "Mario"

        find_one_and_delete_results = await asyncio.gather(
            db.users.find_one_and_delete(user1, filter_by="name"),
            db.users.find_one_and_delete(user2, filter_by="name"),
        )

        find_one_and_set = await asyncio.gather(
            db.users.find_one_and_set(
                user1, exclude="email", filter_by="name", return_old=False
            ),
            db.users.find_one_and_set(
                user2, exclude="email", filter_by="name", return_old=True
            ),
        )

        replace_one_results = await asyncio.gather(
            db.users.replace_one(user2, user3, filter_by="email"),
        )

        ic(
            insert_results,
            set_results,
            find_results,
            find_one_and_replace_results,
            find_one_and_update_results,
            find_one_and_delete_results,
            find_one_and_set,
            replace_one_results,
        )

        await db.users.collection.delete_many({})

    asyncio.run(crud())

    db.close()
