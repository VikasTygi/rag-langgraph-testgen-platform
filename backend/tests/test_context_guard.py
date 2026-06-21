# tests/test_context_guard.py

from app.security.context_guard import control_rag_context


def test_blocks_generation_when_no_context():
    result = control_rag_context(
        docs=[],
        user_prompt="Create venue on Ruckus Cloud from login to verification",
        framework="robot",
        user={
            "username": "developer",
            "projects": ["ruckus-cloud"],
            "teams": ["qa-cloud"],
            "repos": ["ruckus-automation"],
            "access_levels": ["internal"],
        },
    )

    assert result["allowed"] is False
    assert result["status"] == "need_more_context"
    assert result["retrieved_context_count"] == 0
    assert "login flow" in result["missing"]
    assert "venue creation keyword" in result["missing"]
    assert "verification logic" in result["missing"]


def test_allows_generation_when_valid_context_exists():
    docs = [
        {
            "content": "Robot keyword for login and venue creation verification",
            "metadata": {
                "framework": "robot",
                "repo": "ruckus-automation",
                "project": "ruckus-cloud",
                "team": "qa-cloud",
                "access_level": "internal",
            },
        }
    ]

    result = control_rag_context(
        docs=docs,
        user_prompt="Create venue on Ruckus Cloud from login to verification",
        framework="robot",
        user={
            "username": "developer",
            "projects": ["ruckus-cloud"],
            "teams": ["qa-cloud"],
            "repos": ["ruckus-automation"],
            "access_levels": ["internal"],
        },
    )

    assert result["allowed"] is True
    assert result["status"] == "context_ready"
    assert result["retrieved_context_count"] == 1
    assert len(result["safe_docs"]) == 1


def test_blocks_wrong_framework_context():
    docs = [
        {
            "content": "Playwright login test",
            "metadata": {
                "framework": "playwright",
                "repo": "ruckus-automation",
                "project": "ruckus-cloud",
                "team": "qa-cloud",
                "access_level": "internal",
            },
        }
    ]

    result = control_rag_context(
        docs=docs,
        user_prompt="Create venue on Ruckus Cloud from login to verification",
        framework="robot",
        user={
            "username": "developer",
            "projects": ["ruckus-cloud"],
            "teams": ["qa-cloud"],
            "repos": ["ruckus-automation"],
            "access_levels": ["internal"],
        },
    )

    assert result["allowed"] is False
    assert result["status"] == "need_more_context"


def test_blocks_unauthorized_repo_context():
    docs = [
        {
            "content": "Robot keyword for venue creation",
            "metadata": {
                "framework": "robot",
                "repo": "secret-automation-repo",
                "project": "ruckus-cloud",
                "team": "qa-cloud",
                "access_level": "internal",
            },
        }
    ]

    result = control_rag_context(
        docs=docs,
        user_prompt="Create venue on Ruckus Cloud from login to verification",
        framework="robot",
        user={
            "username": "developer",
            "projects": ["ruckus-cloud"],
            "teams": ["qa-cloud"],
            "repos": ["ruckus-automation"],
            "access_levels": ["internal"],
        },
    )

    assert result["allowed"] is False
    assert result["status"] == "need_more_context"
