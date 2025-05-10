from datetime import datetime, date
from typing import Literal

import httpx
from pydantic import StringConstraints, BaseModel
from typing_extensions import Annotated, Optional

import json

from sanic_ext import openapi

from src.database import Database


class RelayModel(BaseModel):
    type: Literal["message", "start", "stop", "crash", "join", "leave", "other"]
    content: str
    embed_title: str
    embed_content: str
    name: str


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
        config = json.load(open('./config.json', 'r'))
        webhook_content = {'username': self.name or 'Server',
                           'content': self.content,
                           'embeds': [] if self.type == 'message' else [self.generate_embed()],
                           'attachments': [],
                           'allowed_mentions': {'parse': []}
                           }

        async with httpx.AsyncClient() as client:
            await client.request(method="POST", url=config['webhook_url'], json=webhook_content)
