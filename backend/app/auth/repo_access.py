from fastapi import HTTPException


ACCESS_RANK = {
    "public": 0,
    "internal": 1,
    "restricted": 2,
}


ROLE_REPO_ACCESS = {
    "admin": {
        "projects": ["*"],
        "teams": ["*"],
        "frameworks": ["*"],
        "max_access_level": "restricted",
    },
    "developer": {
        "projects": ["ruckus-cloud"],
        "teams": ["qa-cloud", "qa-api", "qa-ui"],
        "frameworks": ["robot", "pytest", "playwright"],
        "max_access_level": "internal",
    },
    "viewer": {
        "projects": ["ruckus-cloud"],
        "teams": ["qa-cloud"],
        "frameworks": ["robot"],
        "max_access_level": "internal",
    },
    "ci-system": {
        "projects": ["ruckus-cloud"],
        "teams": ["qa-cloud", "qa-api", "qa-ui"],
        "frameworks": ["robot", "pytest", "playwright"],
        "max_access_level": "internal",
    },
}


def _is_allowed(value: str | None, allowed_values: list[str]) -> bool:
    if "*" in allowed_values:
        return True

    if value is None:
        return True

    return value in allowed_values


def get_repo_policy_for_user(user: dict) -> dict:
    role = user.get("role")

    policy = ROLE_REPO_ACCESS.get(role)

    if not policy:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "repo_access_denied",
                "message": f"No repository access policy found for role: {role}",
            },
        )

    return policy


def authorize_repo_access(
    user: dict,
    framework: str | None = None,
    project: str | None = None,
    team: str | None = None,
) -> dict:
    """
    This function does two things:

    1. Blocks obviously unauthorized requests with HTTP 403.
    2. Builds a ChromaDB metadata filter so retrieval only searches allowed chunks.
    """

    policy = get_repo_policy_for_user(user)

    allowed_projects = policy["projects"]
    allowed_teams = policy["teams"]
    allowed_frameworks = policy["frameworks"]
    max_access_level = policy["max_access_level"]
    max_access_rank = ACCESS_RANK[max_access_level]

    if not _is_allowed(project, allowed_projects):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "project_access_denied",
                "message": f"User is not allowed to access project: {project}",
            },
        )

    if not _is_allowed(team, allowed_teams):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "team_access_denied",
                "message": f"User is not allowed to access team: {team}",
            },
        )

    if not _is_allowed(framework, allowed_frameworks):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "framework_access_denied",
                "message": f"User is not allowed to access framework: {framework}",
            },
        )

    filters = []

    if framework:
        filters.append({"framework": {"$eq": framework}})

    if project:
        filters.append({"project": {"$eq": project}})
    elif "*" not in allowed_projects:
        filters.append({"project": {"$in": allowed_projects}})

    if team:
        filters.append({"team": {"$eq": team}})
    elif "*" not in allowed_teams:
        filters.append({"team": {"$in": allowed_teams}})

    if "*" not in allowed_frameworks and not framework:
        filters.append({"framework": {"$in": allowed_frameworks}})

    filters.append({"access_rank": {"$lte": max_access_rank}})

    if len(filters) == 1:
        return filters[0]

    return {"$and": filters}