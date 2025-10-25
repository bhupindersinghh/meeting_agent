import datetime
from typing import Optional

from pydantic import BaseModel


class Session(BaseModel):
    id: str
    name: str
    description: str
    start_date: datetime.datetime
    end_date: datetime.datetime
    status: Optional[str] = None

class CreateSessionRequest(BaseModel):
    name: str
    description: str