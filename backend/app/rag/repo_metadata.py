from pathlib import Path


ACCESS_RANK = {
    "public": 0,
    "internal": 1,
    "restricted": 2,
}


REPO_METADATA_RULES = [
    {
        "path_contains": "sample_repos/robot",
        "framework": "robot",
        "project": "ruckus-cloud",
        "team": "qa-cloud",
        "access_level": "internal",
    },
    {
        "path_contains": "sample_repos/playwright",
        "framework": "playwright",
        "project": "ruckus-cloud",
        "team": "qa-ui",
        "access_level": "internal",
    },
    {
        "path_contains": "sample_repos/python",
        "framework": "pytest",
        "project": "ruckus-cloud",
        "team": "qa-api",
        "access_level": "internal",
    },
]


def resolve_repo_metadata(file_path: str, default_framework: str = "generic") -> dict:
    normalized_path = str(Path(file_path)).replace("\\", "/")

    for rule in REPO_METADATA_RULES:
        if rule["path_contains"] in normalized_path:
            access_level = rule["access_level"]

            return {
                "source": normalized_path,
                "framework": rule["framework"],
                "project": rule["project"],
                "team": rule["team"],
                "access_level": access_level,
                "access_rank": ACCESS_RANK[access_level],
            }

    return {
        "source": normalized_path,
        "framework": default_framework,
        "project": "unknown",
        "team": "unknown",
        "access_level": "restricted",
        "access_rank": ACCESS_RANK["restricted"],
    }