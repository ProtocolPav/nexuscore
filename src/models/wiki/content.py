import json
from datetime import datetime

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Optional, Annotated

from src.models.users.user import UserOut

ContentID = Annotated[int, Field(
    description="The unique content version ID",
    examples=[1]
)]
PageID = Annotated[int, Field(
    description="The page this content belongs to",
    examples=[321]
)]
Version = Annotated[int, Field(
    description="The version number, scoped per page",
    examples=[3]
)]
EditedByID = Annotated[int, Field(
    description="The ThornyID of the user who edited this content",
    examples=[12]
)]
EditorType = Annotated[str, Field(
    description="The editor type used to create this content",
    examples=['blocknote']
)]
ChangeNote = Annotated[str, Field(
    description="A note describing what changed in this version",
    examples=['Fixed typo in introduction']
)]
Content = Annotated[list[dict], Field(
    description="The full React editor document as an opaque JSON object",
)]
CreatedAt = Annotated[datetime, Field(
    description="When this version was created",
    examples=['2024-07-05 15:15:00+00:00']
)]


class ContentDB(BaseModel):
    content_id: ContentID
    page_id: PageID
    version: Version
    edited_by: EditedByID
    editor_type: EditorType
    change_note: ChangeNote
    content: Content
    created_at: CreatedAt

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('content'), str):
            data['content'] = json.loads(data['content'])

        return data


class ContentOut(BaseModel):
    version: Version
    edited_by: UserOut
    editor_type: EditorType
    change_note: ChangeNote
    data: Content


class ContentIn(BaseModel):
    page_id: PageID
    edited_by: EditedByID
    editor_type: EditorType
    change_note: ChangeNote
    data: Content
