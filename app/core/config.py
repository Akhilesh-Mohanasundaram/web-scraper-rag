from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Web RAG Scraper"
    
    # Database - Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    POSTGRES_SERVER: str = "localhost" 

    # Database - Neo4j
    NEO4J_URI: str = "neo4j://localhost:7687"
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # Redis (Celery)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # LLM Keys
    OPENAI_API_KEY: str | None = None
    SERPER_API_KEY: str | None = None

    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    class Config:
        env_file = ".env"
        case_sensitive = True
        # ADD THIS LINE:
        extra = "ignore" 

settings = Settings()