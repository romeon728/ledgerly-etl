from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database Settings explicitly mapped to .env keys
    db_host: str = Field(validation_alias="DB_HOST")
    db_port: int = Field(validation_alias="DB_PORT")
    db_name: str = Field(validation_alias="DB_NAME")
    db_user: str = Field(validation_alias="DB_USER")
    db_password: str = Field(validation_alias="DB_PASSWORD")

    # Local vLLM Inference Engine explicitly mapped to .env keys
    vllm_base_url: str = Field(validation_alias="VLLM_BASE_URL")
    vllm_model_name: str = Field(validation_alias="VLLM_MODEL_NAME")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Singleton instance to import across the app
settings = Settings()
