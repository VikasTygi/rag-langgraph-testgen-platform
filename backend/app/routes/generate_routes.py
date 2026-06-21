from fastapi import APIRouter, HTTPException

from app.graph.workflow import TestGenerationWorkflow
from app.models import GenerateRequest, GenerateResponse
from fastapi import Depends
from app.auth.dependencies import require_permission
from app.security.prompt_guard import validate_prompt


router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
def generate_test_script(request: GenerateRequest,  current_user: dict = Depends(require_permission("generate:test"))):
    
    guard_result = validate_prompt(request.user_prompt)
    if not guard_result["allowed"]:
        raise HTTPException(
            status_code=403,
            detail=guard_result,
        )
    
    try:
        workflow = TestGenerationWorkflow()
        safe_top_k = min(request.top_k, 5)

        result = workflow.run(
            user_prompt=request.user_prompt,
            framework=request.framework,
            top_k=safe_top_k,
            user=current_user,
        )
        return GenerateResponse(**result)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
