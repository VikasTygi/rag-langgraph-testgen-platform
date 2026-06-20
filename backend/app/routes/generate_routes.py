from fastapi import APIRouter, HTTPException

from app.graph.workflow import TestGenerationWorkflow
from app.models import GenerateRequest, GenerateResponse

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
def generate_test_script(request: GenerateRequest):
    try:
        workflow = TestGenerationWorkflow()

        result = workflow.run(
            user_prompt=request.prompt,
            framework=request.framework,
            top_k=request.top_k,
        )

        return GenerateResponse(**result)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))