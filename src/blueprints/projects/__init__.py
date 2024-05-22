from sanic import Blueprint, Request, HTTPResponse
from sanic import json as sanicjson
from sanic_ext import openapi

from src import model_factory
from src.models import objects, project

import re

project_blueprint = Blueprint("project_routes", url_prefix='/projects')


@project_blueprint.route('/', methods=['POST'])
@openapi.definition(body={'application/json': project.ProjectCreateModel.model_json_schema()})
@openapi.response(status=200,
                  description='Return Project',
                  content={'application/json': objects.ProjectObject.model_json_schema(
                      ref_template="#/components/schemas/{model}"
                    )
                  })
async def create_project(request: Request):
    """
    Create Project

    Creates a new project with the data provided.
    """
    model = project.ProjectCreateModel(**request.json)

    # Transform project name into an ID string,
    # which has the following limits:
    # - Must be lowercase
    # - Only alphanumeric characters and underscores
    project_id = re.sub(r'[^a-z0-9_]', '', model.name.lower().replace(' ', '_'))

    try:
        await model_factory.ProjectFactory.build_project_model(project_id)
        return HTTPResponse(status=500, body="Project already exists!")
    except TypeError:
        await model_factory.ProjectFactory.create_project(project_id, model)

        project_model = await model_factory.ProjectFactory.build_project_model(project_id)
        content_model = await model_factory.ProjectFactory.build_content_model(project_id)
        status_model = await model_factory.ProjectFactory.build_status_model(project_id)
        members_model = await model_factory.ProjectFactory.build_members_model(project_id)

        project_data = project_model | content_model | status_model | members_model

        return sanicjson(objects.ProjectObject(**project_data).dict(), default=str)


@project_blueprint.route('/', methods=['GET'])
@openapi.parameter('users-as-object', bool)
@openapi.response(status=501)
async def get_all_projects(request: Request):
    """
    Get All Projects

    Get all projects as a list of objects.

    By default, the `lead` and `members` of the project are
    returned as ThornyIDs, however you can specify in the URL
    parameter to get a bare-bones User object for each member instead.
    """
    project_ids = await model_factory.ProjectFactory.fetch_all_project_ids()
    projects = []

    for proj in project_ids:
        project_model = await model_factory.ProjectFactory.build_project_model(proj)
        content_model = await model_factory.ProjectFactory.build_content_model(proj)
        status_model = await model_factory.ProjectFactory.build_status_model(proj)
        members_model = await model_factory.ProjectFactory.build_members_model(proj)

        project_data = project_model | content_model | status_model | members_model

        projects.append(objects.ProjectObject(**project_data).dict())
    return sanicjson(projects, default=str)


@project_blueprint.route('/<project_id:str>', methods=['GET'])
@openapi.response(status=200,
                  description='Return Project',
                  content={'application/json': objects.ProjectObject.model_json_schema(
                      ref_template="#/components/schemas/{model}"
                    )
                  })
@openapi.parameter('users-as-object', bool)
async def get_project(request: Request, project_id: str):
    """
    Get Project

    Get the project and its info based on the ID provided.
    Project IDs are strings.

    By default, users are returned as ThornyIDs (`int`), but you can specify
    using `users-as-object=true` to return them as User Objects instead
    """
    project_model = await model_factory.ProjectFactory.build_project_model(project_id)
    content_model = await model_factory.ProjectFactory.build_content_model(project_id)
    status_model = await model_factory.ProjectFactory.build_status_model(project_id)
    members_model = await model_factory.ProjectFactory.build_members_model(project_id)

    project_data = project_model | content_model | status_model | members_model

    if request.args.get('users-as-object', 'false').lower() == 'true':
        project_data['members'] = []
        for member in members_model['members']:
            project_data['members'].append(await model_factory.UserFactory.build_user_model(member))

        project_data['owner_id'] = await model_factory.UserFactory.build_user_model(project_model['owner_id'])
        project_data['content_edited_by'] = await model_factory.UserFactory.build_user_model(content_model['content_edited_by'])

    return sanicjson(objects.ProjectObject(**project_data).dict(), default=str)


@project_blueprint.route('/<project_id:str>', methods=['PATCH'])
@openapi.body(content={'application/json': project.ProjectModel.model_json_schema(
                                            ref_template="#/components/schemas/{model}")})
@openapi.response(status=200, description='Returns Bare Project',
                  content={'application/json': objects.ProjectModel.model_json_schema(
                                                ref_template="#/components/schemas/{model}")})
async def update_project(request: Request, project_id: str):
    """
    Update Project

    Update the project. You do not have to include every field in
    the body, only those that you wish to update.

    Note: ProjectID will not update even if specified.
    """
    model = project.ProjectUpdateModel.parse_obj(request.json).dict()

    model['project_id'] = None

    project_existing = await model_factory.ProjectFactory.build_project_model(project_id)

    project_existing.update([k, v] for k, v in model.items() if v is not None)

    updated_project = objects.ProjectModel(**project_existing)

    await model_factory.ProjectFactory.update_project_model(project_id, updated_project)

    return sanicjson(updated_project.dict(), default=str)


@project_blueprint.route('/<project_id:str>/status', methods=['POST'])
@openapi.body(content={'application/json': {'status': str}})
@openapi.response(status=201, description='Successfully Added')
async def project_status(request: Request, project_id: str):
    """
    New Project Status

    Insert a new project status.
    """
    await model_factory.ProjectFactory.insert_status(project_id, request.json['status'])

    return HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/content', methods=['POST'])
@openapi.body(content={'application/json': {'content': str, 'edited_by': int}})
@openapi.response(status=201, description='Successfully Added')
async def project_content(request: Request, project_id: str):
    """
    New Project Content

    Insert a new project content. `edited_by` is a ThornyID and is required
    """
    await model_factory.ProjectFactory.insert_content(project_id, request.json['content'], request.json['edited_by'])

    return HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/members', methods=['POST'])
@openapi.body(content={'application/json': {'members': list[int]}})
async def update_members(request: Request, project_id: str):
    """
    New Project Members

    Insert new members into the project. Must be ThornyIDs
    """
    await model_factory.ProjectFactory.insert_members(project_id, request.json['members'])

    return HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/members', methods=['DELETE'])
@openapi.response(status=501, description="Not Implemented")
async def delete_members(request: Request, project_id: str):
    """
    Remove Project Members

    Remove existing project members from the project member list.
    """
    return HTTPResponse(status=501)
