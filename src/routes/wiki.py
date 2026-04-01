from sanic import Blueprint, Request, HTTPResponse
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.database import Database
from src.models.wiki import page, content
from src.models.users import user
from src.utils.errors import BadRequest400, NotFound404, Forbidden403

wiki_blueprint = Blueprint("wiki", url_prefix='/wiki')


@wiki_blueprint.route('/pages', methods=['GET'])
@openapi.definition(response=[
    Response(page.PagesListModel.doc_schema(), 200)
])
async def get_all_pages(request: Request, db: Database):
    """
    Get All Wiki Pages

    Get a list of wiki pages, optionally filtered by category and published status.
    """
    category = request.args.get('category')
    published = request.args.get('published', 'true').lower() == 'true'

    pages_model = await page.PagesListModel.fetch(db, category=category, published_only=published)

    return sanic.json(pages_model.model_dump(), default=str)


@wiki_blueprint.route('/pages', methods=['POST'])
@openapi.definition(body=RequestBody(page.PageCreateModel.doc_schema()),
                    response=[
                        Response(page.PageModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=page.PageCreateModel)
async def create_page(request: Request, db: Database, body: page.PageCreateModel):
    """
    Create Wiki Page

    Creates a new wiki page.
    """
    page_id = await page.PageModel.create(db, body)
    page_model = await page.PageModel.fetch(db, page_id, include_content=False)

    return sanic.json(status=201, body=page_model.model_dump(), default=str)


@wiki_blueprint.route('/pages/<page_id:str>', methods=['GET'])
@openapi.definition(response=[
    Response(page.PageModel.doc_schema(), 200),
    Response(NotFound404, 404)
])
async def get_page(request: Request, db: Database, page_id: str):
    """
    Get Wiki Page

    Returns the wiki page specified, with the latest content embedded.
    """
    page_model = await page.PageModel.fetch(db, page_id, include_content=True)

    return sanic.json(page_model.model_dump(), default=str)


@wiki_blueprint.route('/pages/<page_id:str>', methods=['PATCH'])
@openapi.definition(body=RequestBody(page.PageUpdateModel.doc_schema()),
                    response=[
                        Response(page.PageModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=page.PageUpdateModel)
async def update_page(request: Request, db: Database, page_id: str, body: page.PageUpdateModel):
    """
    Update Wiki Page

    Update the wiki page metadata. Anything that you do not want to update can be left as `null`.
    """
    page_model = await page.PageModel.fetch(db, page_id, include_content=False)
    await page_model.update(db, body)

    return sanic.json(page_model.model_dump(), default=str)


@wiki_blueprint.route('/pages/<page_id:str>/content', methods=['POST'])
@openapi.definition(body=RequestBody(content.PageContentCreateModel.doc_schema()),
                    response=[
                        Response(content.PageContentModel.doc_schema(), 201),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404),
                        Response(Forbidden403, 403)
                    ])
@validate(json=content.PageContentCreateModel)
async def create_page_content(request: Request, db: Database, page_id: str, body: content.PageContentCreateModel):
    """
    Create Page Content Version

    Saves a new content version for the specified wiki page. If the page is locked,
    only the author or users with Admin/Owner role can edit.
    """
    page_model = await page.PageModel.fetch(db, page_id, include_content=False)

    if page_model.locked:
        editor = await user.UserModel.fetch(db, body.edited_by)
        if body.edited_by != page_model.author_id and editor.role not in ('Admin', 'Owner'):
            raise Forbidden403()

    content_model = await content.PageContentModel.create(db, page_id, body)

    return sanic.json(status=201, body=content_model.model_dump(), default=str)


@wiki_blueprint.route('/pages/<page_id:str>/content/history', methods=['GET'])
@openapi.definition(response=[
    Response(content.PageContentHistoryModel.doc_schema(), 200),
    Response(NotFound404, 404)
])
async def get_page_content_history(request: Request, db: Database, page_id: str):
    """
    Get Page Content History

    Returns all content versions for the specified wiki page, ordered by version descending.
    """
    history_model = await content.PageContentHistoryModel.fetch(db, page_id)

    return sanic.json(history_model.model_dump(), default=str)


@wiki_blueprint.route('/pages/<page_id:str>/content/<version:int>', methods=['GET'])
@openapi.definition(response=[
    Response(content.PageContentModel.doc_schema(), 200),
    Response(NotFound404, 404)
])
async def get_page_content_version(request: Request, db: Database, page_id: str, version: int):
    """
    Get Page Content Version

    Returns a specific content version for the specified wiki page.
    """
    content_model = await content.PageContentModel.fetch_by_version(db, page_id, version)

    return sanic.json(content_model.model_dump(), default=str)


@wiki_blueprint.route('/pages/<page_id:str>/view', methods=['POST'])
@openapi.definition(response=[
    Response(status=204, description='View count incremented')
])
async def increment_page_views(request: Request, db: Database, page_id: str):
    """
    Increment Page Views

    Increments the view count of the specified wiki page.
    """
    page_model = await page.PageModel.fetch(db, page_id, include_content=False)
    await page_model.increment_views(db)

    return HTTPResponse(status=204)
