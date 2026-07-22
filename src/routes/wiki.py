from typing import Annotated

from fastapi import APIRouter, Query, Security, Depends, status

from src.dependencies.auth import get_guild_client
from src.dependencies.services import get_wiki_service
from src.models.auth import TokenPayload, Scope

from src.models.wiki.page import PageIn, PageOut, PageQuery, PageUpdate
from src.services.wiki import WikiService

wiki_router = APIRouter(prefix='/guilds/me/wiki', tags=['Wiki Pages'])


@wiki_router.get('')
async def list_wiki_pages(
        filter_query: Annotated[PageQuery, Query()],
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WIKI_READ]),
        service: WikiService = Depends(get_wiki_service),
) -> list[PageOut]:
    """
    Get a list of Wiki Pages
    """
    return await service.get_all(auth.guild_id, filter_query)


@wiki_router.post('', status_code=status.HTTP_201_CREATED)
async def create_wiki_page(
        body: PageIn,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WIKI_WRITE]),
        service: WikiService = Depends(get_wiki_service)
) -> PageOut:
    """
    Creates a new wiki page
    """
    return await service.new(auth.guild_id, body)


@wiki_router.get('/{slug}')
async def get_wiki_page(
        slug: str,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WIKI_READ]),
        service: WikiService = Depends(get_wiki_service)
) -> PageOut:
    """
    Returns a wiki page
    """
    return await service.get_by_slug(auth.guild_id, slug)


@wiki_router.patch('/{slug}')
@wiki_router.put('/{slug}')
async def partial_update_wiki_page(
        slug: str,
        body: PageUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WIKI_WRITE]),
        service: WikiService = Depends(get_wiki_service)
) -> PageOut:
    """
    Returns a wiki page
    """
    return await service.update(auth.guild_id, slug, body)

