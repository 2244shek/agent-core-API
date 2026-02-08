from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Core API Settings
    PROJECT_NAME: str = "Agentic Insight Engine"
    API_V1_STR: str = "/api/v1"
    
    # Credentials (will be pulled from .env)
    GROQ_API_KEY: str
    DATABASE_URL: str
    
    # LangChain / LangSmith
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "agent-core-insight-engine"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    TAVILY_API_KEY: str  
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()