from pydantic import BaseModel


class PresignIn(BaseModel):
    filename: str
    content_type: str

class PresignOut(BaseModel):
    upload_url: str
    key: str
    public_url: str