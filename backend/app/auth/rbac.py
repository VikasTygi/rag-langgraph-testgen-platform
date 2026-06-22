from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    CI_SYSTEM = "ci-system"


ROLE_PERMISSIONS = {
    "admin": [
        "rag:ingest",
        "rag:search",
        "generate:test",
        "execute:test",
        "manage:users",
    ],
    "developer": [
        "rag:search",
        "generate:test",
    ],
    "viewer": [
        "rag:search",
    ],
    "ci-system": [
        "rag:search",
        "generate:test",
        "execute:test",
    ],
}


def has_permission(role: str, permission: str) -> bool:
    try:
        role_enum = Role(role)
    except ValueError:
        return False

    return permission in ROLE_PERMISSIONS.get(role_enum, set())