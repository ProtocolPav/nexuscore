from fastapi import HTTPException, status


class NexusException(HTTPException):
    """Base for all Nexuscore exceptions."""
    pass


class NotFound(NexusException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "resource": resource.lower(),
                "message": f"{resource} not found."
            }
        )


class AlreadyExists(NexusException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "already_exists",
                "resource": resource.lower(),
                "message": f"{resource} already exists."
            }
        )


class InsufficientPermissions(NexusException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "You do not have permission to perform this action."
            }
        )


class InvalidCredentials(NexusException):
    def __init__(self, authenticate_value: str = "Bearer"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_credentials",
                "message": "Could not validate credentials."
            },
            headers={"WWW-Authenticate": authenticate_value}
        )


class TokenExpired(NexusException):
    def __init__(self, authenticate_value: str = "Bearer"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "token_expired",
                "message": "The access token has expired."
            },
            headers={"WWW-Authenticate": authenticate_value}
        )


class MissingScope(NexusException):
    def __init__(self, scope: str, authenticate_value: str = "Bearer"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "missing_scope",
                "scope": scope,
                "message": f"Missing required scope: {scope}."
            },
            headers={"WWW-Authenticate": authenticate_value}
        )


class GuildScopedTokenRequired(NexusException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "guild_scoped_token_required",
                "message": "This endpoint requires a guild-scoped token. Request a new token with a guild_id specified."
            }
        )