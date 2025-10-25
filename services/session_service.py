from datetime import datetime, timedelta
import uuid
from models.session_models import CreateSessionRequest, Session


def create_session(request: CreateSessionRequest):
    return Session(
        id = str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(hours=1),
        status='active'
    )