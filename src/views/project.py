from src.database import Database
from src.models.project import ProjectModel, StatusModel, MembersModel, ContentModel, ProjectUpdateModel

from pydantic import BaseModel, model_serializer

import re


class ProjectView(BaseModel):
    project: ProjectModel
    members: MembersModel
    status: StatusModel
    content: ContentModel

    @classmethod
    async def exists(cls, db: Database, project_id: str):
        data = await db.pool.fetchrow("""
                                       SELECT project_id FROM projects.project
                                       WHERE project_id = $1
                                       """,
                                      project_id)

        return data['project_id']

    @classmethod
    async def build(cls, db: Database, project_id: str):
        project = await ProjectModel.fetch(db, project_id)
        member_list = await MembersModel.fetch(db, project_id)
        status = await StatusModel.fetch(db, project_id)
        content = await ContentModel.fetch(db, project_id)

        return cls(project=project, members=member_list, status=status, content=content)

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")

    @classmethod
    async def new(cls, db: Database, model: ProjectUpdateModel):
        project_id = re.sub(r'[^a-z0-9_]', '', model.name.lower().replace(' ', '_'))

        await db.pool.execute("""
                                with project_table as (
                                    insert into projects.project(project_id,
                                                                 name, 
                                                                 description, 
                                                                 coordinates_x, 
                                                                 coordinates_y, 
                                                                 coordinates_z,
                                                                 owner_id)
                                    values($1, $2, $3, $4, $5, $6, $7)
                                ),
                                members_table as (
                                    insert into projects.members(project_id, user_id)
                                    values($1, $7)
                                ),
                                status_table as (
                                    insert into projects.status(project_id, status)
                                    values($1, 'pending')
                                )
                                insert into projects.content(project_id, content, user_id)
                                values($1, '<p>Looking really empty in here. You should totally write up this page, yo!</p>', $7)
                               """,
                              project_id, model.name, model.description, model.coordinates_x,
                              model.coordinates_y, model.coordinates_z, model.owner_id)

        return project_id

    @classmethod
    async def fetch_all_project_ids(cls):
        projects_record = await cls.pool.fetchrow("""
                                                  select array_agg(project_id) as all_projects from projects.project
                                                  """)

        return [i for i in projects_record['all_projects']]
