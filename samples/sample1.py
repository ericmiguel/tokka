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
    user = UserProfile(name="John Doe", email="john.doe@example.com.br")

    async def tokka_crud() -> None:
        messages = await asyncio.gather(
            db.user_profiles.insert_one(user),
            db.user_profiles.insert_one(user, exclude="name"),
            db.user_profiles.set(user, match="name", upsert=True, exclude="email"),
        )

        ic(messages)

    asyncio.run(tokka_crud())
    db.close()
