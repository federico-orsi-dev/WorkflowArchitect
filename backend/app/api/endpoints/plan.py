from fastapi import APIRouter

from app.llm.planner_service import PlannerService
from app.schemas.plan import PlanRequest, PlanResponse

router = APIRouter()
service = PlannerService()


@router.post(
    "/plan",
    response_model=PlanResponse,
    summary="Generate a MicroPlanner plan",
    description="Takes a prompt and returns a concise plan with steps and rationale.",
)
def create_plan(request: PlanRequest) -> PlanResponse:
    result = service.run(request.prompt)
    return PlanResponse(input=request.prompt, result=result)