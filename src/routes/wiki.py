from typing import Annotated

from fastapi import APIRouter, Query, Security, Depends, status

from src.dependencies.auth import get_guild_client
from src.dependencies.services import get_wiki_service
from src.models.auth import TokenPayload, Scope

from src.models.wiki.page import PageOut
from src.services.wiki import WikiService

wiki_router = APIRouter(prefix='/guilds/me/wiki', tags=['Wiki Pages'])


@wiki_router.get('')
async def list_wiki_pages(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: WikiService = Depends(get_wiki_service),
) -> list[PageOut]:
    """
    Get a list of Wiki Pages
    """
    return await service.get_all(auth.guild_id)


@wiki_router.get('/{page_id}')
async def get_wiki_page(
        page_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: WikiService = Depends(get_wiki_service)
) -> PageOut:
    """
    Returns a wiki page
    """
    return await service.get(auth.guild_id, page_id)

