import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import settings
from ...db.database import get_db
from ...services.copilot_service import CopilotQueryService
from .auth import verify_access_token

router = APIRouter()
logger = logging.getLogger("trinetra.copilot")
_request_times: dict[str, list[float]] = {}
_RATE_LIMIT = 30
_RATE_WINDOW_SECONDS = 60


class CopilotChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
    vehicle_number: str | None = Field(default=None, max_length=30)
    camera_id: int | None = Field(default=None, ge=1)
    start_date: str | None = Field(default=None, max_length=30)
    end_date: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=120)
    alert_status: str | None = Field(default=None, max_length=30)
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int = Field(default=50, ge=1, le=200)


@router.post("/chat")
def chat_with_copilot(
    payload: CopilotChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.split(" ", 1)[1].strip()
    if not verify_access_token(token):
        raise HTTPException(status_code=401, detail="Authentication required")

    client_key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    recent_requests = [timestamp for timestamp in _request_times.get(client_key, []) if now - timestamp < _RATE_WINDOW_SECONDS]
    if len(recent_requests) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Copilot request limit reached; try again shortly")
    recent_requests.append(now)
    _request_times[client_key] = recent_requests

    logger.info("copilot_query operator=authenticated ip=%s", request.client.host if request.client else "unknown")
    service = CopilotQueryService(db)
    result = service.handle_question(
        payload.message,
        vehicle_number=payload.vehicle_number,
        camera_id=payload.camera_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        location=payload.location,
        alert_status=payload.alert_status,
        page=payload.page,
        page_size=payload.page_size,
    )
    return result
