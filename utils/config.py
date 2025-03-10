from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # llm
    ANALYSIS_LLM_API_KEY: str
    ANALYSIS_LLM_BASE_URL: str
    ANALYSIS_LLM_MODEL: str
    ANALYSIS_LLM_TEMPERATURE: float

    ANSWER_LLM_API_KEY: str
    ANSWER_LLM_BASE_URL: str
    ANSWER_LLM_MODEL: str
    ANSWER_LLM_TEMPERATURE: float

    # search
    BOCHA_API_KEY: str
    BOCHA_NEEDS_CRAWLER: bool = False
    BOCHA_NEEDS_FILTER: bool = False

    # log
    LOG_LEVEL: str = "INFO"


settings = Settings()
