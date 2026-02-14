from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://stockbot:stockbot@localhost:5432/stockbot"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    alpaca_base_url: str = "https://data.alpaca.markets"

    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
