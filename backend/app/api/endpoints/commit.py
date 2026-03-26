from fastapi import APIRouter

from app.schemas.commit import CommitRequest, CommitResponse
from app.services.commit_service import CommitService

router = APIRouter()
service = CommitService()


@router.post(
    "/commit",
    response_model=CommitResponse,
    summary="Generate a CommitSense response",
    description="Takes a change summary and returns a refined summary with a commit message.",
)
def create_commit(request: CommitRequest) -> CommitResponse:
    result = service.run(request.message)
    return CommitResponse(input=request.message, result=result)
