from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./ballify.db"
    web_origin: str = "http://localhost:3000"

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "ballify/0.1"

    odds_api_key: str = ""

    @property
    def reddit_configured(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)

    @property
    def odds_configured(self) -> bool:
        return bool(self.odds_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
