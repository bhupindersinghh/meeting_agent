from services import session_service
from fastapi import APIRouter

from models.session_models import CreateSessionRequest, Session


session_router = APIRouter(prefix="/session", tags=["session"])

@session_router.post("/")
def create_session(request: CreateSessionRequest) -> Session:
    return session_service.create_session(request)