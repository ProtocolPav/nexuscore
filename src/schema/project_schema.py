from dataclasses import dataclass
from datetime import datetime
from typing import Union


@dataclass
class Project:
    project_id: str
    name: str
    coordinates: list[int, int, int]
    description: str
    status: Union[0, 1, 2, 3]
    content: str
    lead_id: int
    member_ids: list[int]
    thread_id: int
    accepted_on: datetime
    completed_on: datetime | None
