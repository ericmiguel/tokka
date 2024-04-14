"""Tokka sample code."""

import asyncio

import config
from icecream import ic
from pydantic import BaseModel
from tokka import Collection
from tokka import Database


# Define a Pydantic model to represent the data
class UserProfile(BaseModel):
    name: str
    email: str


# Create a subclass of Database to define the your collections
class DB(Database):
    @property
    def user_profiles(self) -> Collection:
        return self.get_collection("profiles")


if __name__ == "__main__":
    db = DB("tokka", connection=config.mongodb.URI)
    user1 = UserProfile(name="John Doe", email="john.doe@example.com.br")
    user2 = UserProfile(name="Emma Su", email="ema.sue@example.com.br")
    user3 = UserProfile(name="Joanne Doe", email="joanne.doe@example.com.br")

    async def crud() -> None:
        insert_results = await asyncio.gather(
            db.user_profiles.insert_one(user1),
            db.user_profiles.insert_one(user2),
            db.user_profiles.insert_one(user1, exclude="name"),
        )

        set_results = await asyncio.gather(
            db.user_profiles.set(user1, match="name", upsert=True, exclude="email"),
            db.user_profiles.find_one(user2, filter_by="name"),
        )

        find_results = await asyncio.gather(
            db.user_profiles.find_one(user1, filter_by="name"),
            db.user_profiles.find_one(user2, filter_by="name"),
            db.user_profiles.find_one(user1, filter_by="email"),
        )

        find_one_and_replace_results = await asyncio.gather(
            db.user_profiles.find_one_and_replace(user1, user2, filter_by="name"),
            db.user_profiles.find_one_and_replace(
                user2, user1, filter_by="name", return_old=True
            ),
        )

        find_one_and_update_results = await asyncio.gather(
            db.user_profiles.find_one_and_update(
                user1, {"$set": {"name": "Mario"}}, filter_by="name", return_old=False
            ),
            db.user_profiles.find_one_and_update(
                user2, {"$set": {"name": "Maria"}}, filter_by="name", return_old=True
            ),
        )

        user1.name = "Mario"

        find_one_and_delete_results = await asyncio.gather(
            db.user_profiles.find_one_and_delete(user1, filter_by="name"),
            db.user_profiles.find_one_and_delete(user2, filter_by="name"),
        )

        find_one_and_set = await asyncio.gather(
            db.user_profiles.find_one_and_set(
                user1, exclude="email", filter_by="name", return_old=False
            ),
            db.user_profiles.find_one_and_set(
                user2, exclude="email", filter_by="name", return_old=True
            ),
        )

        replace_one_results = await asyncio.gather(
            db.user_profiles.replace_one(user2, user3, filter_by="email"),
        )

        ic(
            insert_results,
            set_results,
            find_results,
            find_one_and_replace_results,
            find_one_and_update_results,
            find_one_and_delete_results,
            find_one_and_set,
            replace_one_results
            

        )

        await db.user_profiles.collection.delete_many({})

    asyncio.run(crud())

    db.close()
