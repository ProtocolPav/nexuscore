import json
from datetime import datetime

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Optional, Annotated

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


class PageContentBaseModel(BaseModel):
    content: list[dict] = Field(description="The full React editor document as an opaque JSON object",
                                json_schema_extra={"example": []})
    editor_type: str = Field(description="The editor type used to create this content",
                             json_schema_extra={"example": "blocknote"})
    change_note: Optional[str] = Field(description="A note describing what changed in this version",
                                       json_schema_extra={"example": "Fixed typo in introduction"})

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('content'), str):
            data['content'] = json.loads(data['content'])

        return data


@openapi.component()
class PageContentModel(PageContentBaseModel):
    content_id: int = Field(description="The unique content version ID",
                            json_schema_extra={"example": 1})
    page_id: str = Field(description="The page this content belongs to",
                         json_schema_extra={"example": "my_wiki_page"})
    version: int = Field(description="The version number, scoped per page",
                         json_schema_extra={"example": 3})
    edited_by: int = Field(description="The ThornyID of the user who edited this content",
                           json_schema_extra={"example": 12})
    editor: user.UserModel = Field(description="The user who edited this content")
    edited_at: datetime = Field(description="When this version was created",
                                json_schema_extra={"example": "2024-07-05 15:15:00+00:00"})

    @classmethod
    async def create(cls, db: Database, model: "PageContentCreateModel", page_id: str = None, *args) -> "PageContentModel":
        data = await db.pool.fetchrow("""
                                      INSERT INTO wiki.page_content(page_id, content, editor_type, edited_by, change_note, version)
                                      VALUES($1, $2, $3, $4, $5,
                                             COALESCE((SELECT MAX(version)
                                                       FROM wiki.page_content
                                                       WHERE page_id = $1), 0) + 1)
                                      RETURNING *
                                      """,
                                      page_id, json.dumps(model.content, default=str), model.editor_type, model.edited_by, model.change_note)

        await db.pool.execute("""
                              UPDATE wiki.page
                              SET updated_at = now()
                              WHERE page_id = $1
                              """,
                              page_id)

        editor = await user.UserModel.fetch(db, data['edited_by'])
        return cls(**data, editor=editor)

    @classmethod
    async def fetch(cls, db: Database, content_id: int) -> "PageContentModel":
        data = await db.pool.fetchrow("""
                                      SELECT * FROM wiki.page_content
                                      WHERE content_id = $1
                                      """,
                                      content_id)

        if data:
            editor = await user.UserModel.fetch(db, data['edited_by'])
            return cls(**data, editor=editor)
        else:
            raise NotFound404(extra={'resource': 'page_content', 'id': content_id})

    @classmethod
    async def fetch_latest(cls, db: Database, page_id: str) -> Optional["PageContentModel"]:
        data = await db.pool.fetchrow("""
                                      SELECT * FROM wiki.page_content
                                      WHERE page_id = $1
                                      ORDER BY version DESC
                                      LIMIT 1
                                      """,
                                      page_id)

        if data:
            editor = await user.UserModel.fetch(db, data['edited_by'])
            return cls(**data, editor=editor)
        return None

    @classmethod
    async def fetch_by_version(cls, db: Database, page_id: str, version: int) -> "PageContentModel":
        data = await db.pool.fetchrow("""
                                      SELECT * FROM wiki.page_content
                                      WHERE page_id = $1 AND version = $2
                                      """,
                                      page_id, version)

        if data:
            editor = await user.UserModel.fetch(db, data['edited_by'])
            return cls(**data, editor=editor)
        else:
            raise NotFound404(extra={'resource': 'page_content', 'id': f"{page_id}/v{version}"})


class PageContentHistoryModel(BaseList[PageContentModel]):
    @classmethod
    async def fetch(cls, db: Database, page_id: str) -> "PageContentHistoryModel":
        data = await db.pool.fetch("""
                                   SELECT * FROM wiki.page_content
                                   WHERE page_id = $1
                                   ORDER BY version DESC
                                   """,
                                   page_id)

        contents: list[PageContentModel] = []
        for row in data:
            editor = await user.UserModel.fetch(db, row['edited_by'])
            contents.append(PageContentModel(**row, editor=editor))

        return cls(root=contents)


class PageContentCreateModel(PageContentBaseModel):
    edited_by: int = Field(description="The ThornyID of the user creating this content version",
                           json_schema_extra={"example": 12})
