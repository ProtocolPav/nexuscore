from typing import Literal
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

AllowedImageType = Literal[
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
]

Filename = Annotated[
    str,
    StringConstraints(min_length=1, max_length=255, pattern=r"^[\w\-. ]+\.[A-Za-z0-9]+$"),
]

class PresignIn(BaseModel):
    filename: Filename = Field(..., description="Original filename, including extension")
    content_type: AllowedImageType = Field(..., description="MIME type of the file being uploaded")

class PresignOut(BaseModel):
    upload_url: str = Field(..., description="Short-lived presigned PUT URL for uploading directly to R2")
    key: str = Field(..., description="Object key/path in the R2 bucket")
    public_url: str = Field(..., description="Permanent public/CDN URL once the upload completes")