from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class MongoDB(BaseSettings, case_sensitive=False):
    model_config = SettingsConfigDict(env_file=".env.db")
    URI: str = Field(default=...)


mongodb = MongoDB()
