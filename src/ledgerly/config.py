from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # DB Settings
    db_name: str = Field(default="ledgerly_db", validation_alias="DB_NAME")
    db_user: str = Field(default="ledgerly", validation_alias="DB_USER")
    db_password: str = Field(default="ledgerly_local_sec_pass", validation_alias="DB_PASSWORD")
    db_host: str = Field(default="db", validation_alias="DB_HOST")
    db_port: int = Field(default=5432, validation_alias="DB_PORT")
    
    # Local vLLM Settings (Ensures 100% local processing)
    vllm_host: str = Field(default="http://host.docker.internal:8000/v1", validation_alias="VLLM_HOST")
    vllm_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", validation_alias="VLLM_MODEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()