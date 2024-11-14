import re
from datetime import date

from pydantic import BaseModel, Field
from typing_extensions import Optional

from src.database import Database
from src.models import users

from sanic_ext import openapi


@openapi.component()
class ProjectModel(BaseModel):
    project_id: str = Field(description="The id of the project. Comprised of: a-z and underscores",
                            examples=['my_cool_project'])
    name: str = Field(description="The name of the project",
                      examples=['My Cool Project'])
    description: str = Field(description="A short description of the project",
                             examples=['This is a sick project with big houses...'])
    coordinates: tuple[int, int, int] = Field(description="The coordinates of the project",
                                              examples=[[333, 55, -65]])
    thread_id: Optional[int] = Field(description="The discord thread ID of the project",
                                     examples=[134908547047468818])
    started_on: date = Field(description="The date the project was started on",
                             examples=['2024-05-05'])
    completed_on: Optional[date] = Field(description="The date the project was completed on",
                                         examples=['2024-07-05'])
    owner: users.UserModel = Field(description="The owner of the project, in the form of a User object",
                                   examples=[123])

    @classmethod
    async def new(cls, db: Database, project_id: str, model: "ProjectCreateModel"):
        await db.pool.execute("""
                                with project_table as (
                                    insert into projects.project(project_id,
                                                                 name, 
                                                                 description, 
                                                                 coordinates,
                                                                 owner_id,
                                                                 coordinates_x,
                                                                 coordinates_y,
                                                                 coordinates_z)
                                    values($1, $2, $3, $4, $5, 0, 0, 0)
                                ),
                                members_table as (
                                    insert into projects.members(project_id, user_id)
                                    values($1, $5)
                                ),
                                status_table as (
                                    insert into projects.status(project_id, status)
                                    values($1, 'pending')
                                )
                                insert into projects.content(project_id, content, user_id)
                                values($1, '<p>Looking really empty in here. You should totally write up this page, yo!</p>', $5)
                               """,
                              project_id, model.name, model.description, model.coordinates, model.owner_id)

        return project_id

    @classmethod
    async def fetch(cls, db: Database, project_id: str) -> Optional["ProjectModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT * FROM projects.project
                                       WHERE project_id = $1
                                       """,
                                      project_id)

        if data:
            owner = await users.UserModel.fetch(db, data['owner_id'])

            return cls(**data, owner=owner)
        else:
            return None

    @classmethod
    async def fetch_all(cls, db: Database) -> Optional[list["ProjectModel"]]:
        projects_record = await db.pool.fetchrow("""
                                                  select array_agg(project_id) as all_projects from projects.project
                                                  """)

        return [await cls.fetch(db, i) for i in projects_record['all_projects']]

    async def update(self, db: Database):
        await db.pool.execute("""
                               UPDATE projects.project
                               SET name = $1,
                                   thread_id = $2,
                                   coordinates = $3,
                                   description = $4,
                                   completed_on = $5,
                                   owner_id = $6
                               WHERE project_id = $7
                               """,
                              self.name, self.thread_id, self.coordinates,
                              self.description, self.completed_on, self.owner_id, self.project_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class AllProjectsModel(BaseModel):
    projects: list[ProjectModel]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class ProjectCreateModel(BaseModel):
    name: str = Field(description="The name of the project",
                      examples=['My Cool Project'])
    description: str = Field(description="A short description of the project",
                             examples=['This is a sick project with big houses...'])
    coordinates: tuple[int, int, int] = Field(description="The coordinates of the project",
                                              examples=[[333, 55, -65]])
    owner_id: int = Field(description="The ThornyID of the project owner",
                          examples=[44])

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class ProjectUpdateModel(BaseModel):
    name: str = Field(description="The name of the project",
                      examples=['My Cool Project'])
    description: str = Field(description="A short description of the project",
                             examples=['This is a sick project with big houses...'])
    coordinates: tuple[int, int, int] = Field(description="The coordinates of the project",
                                              examples=[[333, 55, -65]])
    thread_id: Optional[int] = Field(description="The discord thread ID of the project",
                                     examples=[134908547047468818])
    started_on: date = Field(description="The date the project was started on",
                             examples=['2024-05-05'])
    completed_on: Optional[date] = Field(description="The date the project was completed on",
                                         examples=['2024-07-05'])
    owner_id: int = Field("The ThornyID of the project owner",
                          examples=[44])

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
