import os
from typing import Literal
import httpx

from pydantic import Field

from src.utils.base import BaseModel
from src.config import settings

class RelayModel(BaseModel):
    type: Literal["message", "start", "stop", "crash", "join", "leave", "other"] = Field(description="The type of relay",
                                                                                         json_schema_extra={"example": "message"})
    content: str = Field(description="The content of the message",
                         json_schema_extra={"example": "Hello, world!"})
    embed_title: str = Field(description="The title of the embed",
                             json_schema_extra={"example": "Title"})
    embed_content: str = Field(description="The content of the embed",
                               json_schema_extra={"example": "Hello, world!"})
    name: str = Field(description="The name to use for the webhook",
                      json_schema_extra={"example": "ProtocolPav"})

    def generate_embed(self):
        if self.type == 'stop':
            return {'title': self.embed_title, 'color': 13763629, 'description': self.embed_content}
        elif self.type == 'start':
            return {'title': self.embed_title, 'color': 776785, 'description': self.embed_content}
        elif self.type == 'crash':
            return {'title': self.embed_title, 'color': 16738740, 'description': self.embed_content}
        elif self.type == 'join':
            return {'title': self.embed_title, 'color': 40544, 'description': self.embed_content}
        elif self.type == 'leave':
            return {'title': self.embed_title, 'color': 14893620, 'description': self.embed_content}
        elif self.type == 'other':
            return {'title': self.embed_title, 'color': 14679808, 'description': self.embed_content}
        return None

    async def relay(self):
        webhook_content = {'username': self.name or 'Server',
                           'content': self.content,
                           'embeds': [] if self.type == 'message' else [self.generate_embed()],
                           'attachments': [],
                           'allowed_mentions': {'parse': []}
                           }

        async with httpx.AsyncClient() as client:
            await client.request(method="POST", url=settings.WEBHOOK_URL, json=webhook_content)