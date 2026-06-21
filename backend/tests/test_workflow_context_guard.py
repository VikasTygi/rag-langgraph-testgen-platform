# tests/test_workflow_context_guard.py

from app.graph.workflow import TestGenerationWorkflow


def test_workflow_blocks_generation_when_no_context():
    workflow = TestGenerationWorkflow()

    result = workflow.run(
        user_prompt="Create venue on Ruckus Cloud from login to verification",
        framework="robot",
        top_k=5,
        user={
            "username": "developer",
            "role": "developer",
            "projects": ["ruckus-cloud"],
            "teams": ["qa-cloud"],
            "repos": ["ruckus-automation"],
            "access_levels": ["internal"],
        },
    )

    if result["retrieved_context_count"] == 0:
        assert result["status"] == "need_more_context"
        assert result["generated_code"] is None
        assert result["valid"] is False
        assert "login flow" in result["missing"]
        assert "venue creation keyword" in result["missing"]
        assert "verification logic" in result["missing"]