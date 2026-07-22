import boto3
from botocore.config import Config
from botocore.client import BaseClient
from src.settings import settings

_r2_client: BaseClient

def init_r2_client():
    global _r2_client
    _r2_client = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY,
        aws_secret_access_key=settings.R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )

def get_r2_client():
    return _r2_client