import re
from datetime import date, datetime

from pydantic import Field
from typing_extensions import Literal, Optional

from src.database import Database
from src.models.users import user
from src.utils.base import BaseModel, BaseList, optional_model

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404


class ProjectBaseModel(BaseModel):
    name: str = Field(description="The name of the project",
                      json_schema_extra={"example": 'My Project'})
    description: str = Field(description="A short description of the project",
                             json_schema_extra={"example": 'This project will have houses'})
    coordinates: list[int] = Field(description="The coordinates of the project",
                                   json_schema_extra={"example": [132, 65, 33]})
    dimension: str = Field(description="The dimension of the project",
                           json_schema_extra={"example": 'minecraft:overworld'})
    owner_id: int = Field(description="The project owner ID",
                          json_schema_extra={"example": 12})
    pin_id: Optional[int] = Field(description="The related pin's ID",
                                  json_schema_extra={"example": 54})


@openapi.component()
class ProjectModel(ProjectBaseModel):
    project_id: str = Field(description="The string ID of the project",
                            json_schema_extra={"example": 'my_project'})
    thread_id: Optional[int] = Field(description="The discord thread ID of the project",
                                     json_schema_extra={"example": 134908547047468818})
    started_on: date = Field(description="The date the project was started on",
                             json_schema_extra={"example": '2024-05-05'})
    completed_on: Optional[date] = Field(description="The date the project was completed on",
                                         json_schema_extra={"example": '2024-05-05'})
    status: Literal["pending", "ongoing", "abandoned", "completed"] = Field(description="The project status",
                                                                            json_schema_extra={"example": 'ongoing'})
    status_since: datetime = Field(description="When the status was last updated",
                                   json_schema_extra={"example": "2024-07-05 15:15:00"})
    owner: user.UserModel = Field(description="The owner of the project, in the form of a User object")

    @classmethod
    async def create(cls, db: Database, model: "ProjectCreateModel", *args) -> str:
        project_id = re.sub(r'[^a-z0-9_]', '', model.name.lower().replace(' ', '_'))

        await db.pool.execute("""
                                with project_table as (
                                    insert into projects.project(project_id,
                                                                 name, 
                                                                 description, 
                                                                 coordinates,
                                                                 owner_id)
                                    values($1, $2, $3, $4, $5)
                                    RETURNING project_id
                                ),
                                members_table as (
                                    insert into projects.members(project_id, user_id)
                                    values($1, $5)
                                ),
                                status_table as (
                                    insert into projects.status(project_id, status)
                                    values($1, 'pending')
                                )
                                SELECT project_id FROM project_table
                               """,
                              project_id, model.name, model.description, model.coordinates, model.owner_id)

        return project_id

    @classmethod
    async def fetch(cls, db: Database, project_id: str, *args) -> "ProjectModel":
        if not project_id:
            raise BadRequest400(extra={'ids': ['project_id']})

        data = await db.pool.fetchrow("""
                                      SELECT p.*, s.status, s.since AS status_since FROM projects.project p
                                      INNER JOIN projects.status s ON p.project_id = s.project_id
                                      WHERE p.project_id = $1
                                      ORDER BY s.since DESC
                                      """,
                                      project_id)

        if data:
            owner = await user.UserModel.fetch(db, data['owner_id'])
            return cls(**data, owner=owner)
        else:
            raise NotFound404(extra={'resource': 'project', 'id': project_id})

    async def update(self, db: Database, model: "ProjectUpdateModel", *args):
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


class ProjectsListModel(BaseList[ProjectModel]):
    @classmethod
    async def fetch(cls, db: Database, *args) -> "ProjectsListModel":
        data = await db.pool.fetch("""
                                    SELECT DISTINCT ON (p.project_id) 
                                           p.*, s.status, s.since AS status_since
                                    FROM projects.project p
                                    JOIN projects.status s ON p.project_id = s.project_id
                                    ORDER BY p.project_id, s.since DESC
                                   """)

        projects: list[ProjectModel] = []
        for project in data:
            owner = await user.UserModel.fetch(db, project['owner_id'])
            projects.append(ProjectModel(**project, owner=owner))

        return cls(root=projects)


class ProjectCreateModel(ProjectBaseModel):
    pass


class ProjectUpdateMixin(ProjectBaseModel):
    thread_id: int = Field(description="The discord thread ID of the project",
                           json_schema_extra={"example": 134908547047468818})
    started_on: date = Field(description="The date the project was started on",
                             json_schema_extra={"example": '2024-05-05'})
    completed_on: date = Field(description="The date the project was completed on",
                               json_schema_extra={"example": '2024-05-05'})


ProjectUpdateModel = optional_model('ProjectUpdateModel', ProjectUpdateMixin)
