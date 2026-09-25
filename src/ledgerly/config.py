from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    bank_name: str = Field(default="TD Bank", validation_alias="BANK")
    bank_rtn: str = Field(..., validation_alias="BANK_RTN")
    checking_account: str = Field(..., validation_alias="CHECKING_ACCOUNT_NUMBER")
    savings_account: str = Field(..., validation_alias="SAVINGS_ACCOUNT_NUMBER")
    
    # DB Settings
    db_name: str = Field(default="ledgerly_db", validation_alias="DB_NAME")
    db_user: str = Field(default="nromeo", validation_alias="DB_USER")
    db_host: str = Field(default="localhost", validation_alias="DB_HOST")
    db_port: int = Field(default=5432, validation_alias="DB_PORT")
    
    # vLLM Integration Settings
    vllm_host: str = Field(default="http://localhost:8000/v1", validation_alias="VLLM_HOST")
    vllm_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", validation_alias="VLLM_MODEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()