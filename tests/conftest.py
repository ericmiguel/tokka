from pydantic import BaseModel
import pytest
from tokka import Client
from tokka import Collection
from tokka import Database


@pytest.fixture(scope="session")
def mongo_uri() -> str:
    return "mongodb://localhost:27017/?replicaSet=tokka"


@pytest.fixture(scope="session")
def client(mongo_uri: str) -> Client:
    return Client(mongo_uri)


@pytest.fixture(scope="session")
def database(client: Client) -> Database:
    return client.get_database("tokka-test-db")


@pytest.fixture(scope="function")
def collection(database: Database) -> Collection:
    return database.get_collection("tokka-test-collection")



class TestUser(BaseModel):
    name: str
    age: int


@pytest.fixture(scope="session")
def user_1() -> TestUser:
    return TestUser(name="John", age=30)

@pytest.fixture(scope="session")
def user_1_update() -> TestUser:
    return TestUser(name="John Doe", age=30)

@pytest.fixture(scope="session")
def user_2() -> TestUser:
    return TestUser(name="Jane", age=25)
