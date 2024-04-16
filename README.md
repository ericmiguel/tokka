<p align="center">
  <a href="https://github.com/ericmiguel/tokka"><img src="https://github.com/ericmiguel/tokka/assets/12076399/09366629-fdb6-46b3-9a3b-6d3c20b8a727" alt="Tokka"></a>
</p>
<p align="center">
    A thin async layer between Pydantic and MongoDB.
</p>
<p align="center">
    <span><a href="https://ericmiguel.github.io/tokka/" target="_blank">[DOCS]</a></span>
    <span><a href="https://github.com/ericmiguel/tokka" target="_blank">[SOURCE]</a></span>
</p>
<p align="center">
<a href="https://pypi.org/project/tokka" target="_blank">
    <img src="https://img.shields.io/pypi/v/tokka?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/tokka" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/tokka.svg?color=%2334D058" alt="Supported Python versions">
</a>
</p>

## What is

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
If you can make some use of it or make you write less code, I'll be glad.


## Installation

```bash
pip install tokka

```

## Quick usage

```python
from pydantic import BaseModel

from tokka import Database
from tokka import Collection

import asyncio


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
    db = DB("sampleDB", connection="YOUR MONGODB URI")
    user1 = User(name="John Doe", email="john.doe@tokka.com.br")
    user2 = User(name="Emma Soo", email="emma.sue@tokka.com.br")

    async def tasks() -> None:
        insert_results = await asyncio.gather(
            db.users.insert_one(user1),
            db.users.find_one(user1, filter_by="name"),
        )

        print(insert_results)

        replace_one_results = await asyncio.gather(
            db.users.replace_one(user1, user2, filter_by="email"),
            db.users.find_one(user2, filter_by="name"),
        )

        print(replace_one_results)

        find_one_and_delete_results = await asyncio.gather(
            db.users.find_one_and_delete(user2, filter_by="name"),
        )

        print(find_one_and_delete_results)
        

    asyncio.run(tasks())
    db.close()
```

## Docs

Tokka is almost a syntatic-sugar package wrapping Motor and Pydantic.

Docstrings and repo samples should be enought to get you running in a few seconds.

## Benchmarking

Formal benchmarks are still necessary, but initial executions showed an impact of less
than <0.1s using Tokka.

## License

This project is licensed under the terms of the MIT license.
