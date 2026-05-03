from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "eu-central-1"
    dynamodb_endpoint_url: str | None = None
    dynamodb_table_name: str = "hrs"


settings = Settings()
