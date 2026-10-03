
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

class DetailedHealthResponse(BaseModel):
    status: str
    services: dict[str, str]
