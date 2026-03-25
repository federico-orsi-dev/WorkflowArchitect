from fastapi import APIRouter

from app.services.pr_service import PullRequestService
from app.schemas.pr import PullRequestRequest, PullRequestResponse

router = APIRouter()
service = PullRequestService()


@router.post(
    "/pr",
    response_model=PullRequestResponse,
    summary="Aggregate multiple commits into a pull request",
    description="Takes commit results and returns a unified PR title, body, changelog, and labels.",
)
def create_pull_request(request: PullRequestRequest) -> PullRequestResponse:
    result = service.run(request.commits)
    return PullRequestResponse(input=request.commits, result=result)
