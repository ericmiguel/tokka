"""Tokka sample code."""

import asyncio

from pydantic import BaseModel
from tokka import Collection
from tokka import Database
from icecream import ic
import config

# Define a Pydantic model to represent the data
class User(BaseModel):
    name: str
    email: str

# Create a subclass of Database to define the your collections
class MyDB(Database):
    @property
    def profiles(self) -> Collection:
        return self.get_collection("profiles")

# Define some operations
async def set(coll: Collection) -> str:
    await coll.set(user, match="name", upsert=True, exclude="email")
    return f"set: done!"

async def insert(coll: Collection) -> str:
    await coll.insert_one(user)
    await coll.insert_one(user, exclude="name")
    return f"insert: done!"


if __name__ == "__main__":
    mydb = MyDB("tokka", connection=config.mongodb.URI)
    user = User(name="John Doe", email="john.doe@example.com.br")

    async def main() -> None:
        collection = mydb.profiles
        messages = await asyncio.gather(set(collection), insert(collection))
        ic(messages)

    asyncio.run(main())
    mydb.close()
