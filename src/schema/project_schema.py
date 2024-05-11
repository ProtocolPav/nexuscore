from dataclasses import dataclass
from datetime import datetime
from typing import Union

import asyncpg


@dataclass
class Project:
    project_id: str
    name: str
    coordinates: list[int]
    description: str
    status: Union[0, 1, 2, 3]
    content: str
    lead_user: int
    member_users: list[int]
    thread_id: int
    accepted_on: datetime
    completed_on: datetime | None

    @classmethod
    def build(cls, data: asyncpg.Record):
        return cls(project_id=data['project_id'],
                   name=data['name'],
                   coordinates=[int(x) for x in data['coordinates'].split(', ')],
                   description=data['description'],
                   status=data['status'],
                   content=None,
                   lead_user=data['owner_id'],
                   member_users=[int(x) for x in data['members'].split(', ')],
                   thread_id=data['thread_id'],
                   accepted_on=data['accepted_on'],
                   completed_on=data['completed_on'])
        
