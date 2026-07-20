from fastapi import APIRouter, Depends

from src.dependencies.services import get_image_service
from src.models.image import PresignIn, PresignOut
from src.services.image import ImageService

image_router = APIRouter(prefix="/uploads", tags=["uploads"])

@image_router.post("/presign")
async def get_presigned_upload_url(
        body: PresignIn,
        service: ImageService = Depends(get_image_service),
) -> PresignOut:
    return service.create_presigned_upload(body.filename, body.content_type)