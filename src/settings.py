from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    TOKEN_TTL_SECONDS: int = 3600
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    WEBHOOK_URL: str
    R2_ACCESS_KEY: str
    R2_SECRET_KEY: str
    R2_ACCOUNT_ID: str
    R2_BUCKET_NAME: str

settings = Settings()