from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    CI_SYSTEM = "ci-system"


ROLE_PERMISSIONS = {
    Role.ADMIN: {
        "rag:ingest",
        "rag:search",
        "generate",
        "execute",
        "delete_collection",
        "manage_users",
    },
    Role.DEVELOPER: {
        "rag:search",
        "generate:test",
        "generate",
        "rag:ingest",
    },
    Role.VIEWER: {
        "rag:search",
    },
    Role.CI_SYSTEM: {
        "generate",
        "validate",
        "execute",
        "rag:ingest",
    },
}


def has_permission(role: str, permission: str) -> bool:
    try:
        role_enum = Role(role)
    except ValueError:
        return False

    return permission in ROLE_PERMISSIONS.get(role_enum, set())