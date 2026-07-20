import uuid
from datetime import datetime
from src.models.image import PresignOut
from src.settings import settings


class ImageService:
    def __init__(self, r2_client):
        self.client = r2_client

    @staticmethod
    def _generate_key(filename: str, prefix: str = "wiki") -> str:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        date_path = datetime.utcnow().strftime("%Y/%m")
        return f"{prefix}/{date_path}/{uuid.uuid4()}.{ext}"

    def create_presigned_upload(
            self, filename: str, content_type: str, expires_in: int = 300
    ) -> PresignOut:
        key = self._generate_key(filename)

        upload_url = self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )

        return PresignOut(
            upload_url=upload_url,
            key=key,
            public_url=f"https://cdn.everthorn.net/{key}",
        )