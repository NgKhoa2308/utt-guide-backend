from pydantic import BaseModel
from app.location.models import LocationStatus

class CreateLocationCommand(BaseModel):
    name: str
    description: str | None = None
    lat: float
    lng: float
    photo_url: str | None = None
    min_price: int | None = None
    max_price: int | None = None

class LocationResponseDTO(BaseModel):
    id: int
    name: str
    description: str | None
    photo_url: str | None
    lat: float
    lng: float
    min_price: int | None
    max_price: int | None
    status: LocationStatus
    like_count: int

    class Config:
        from_attributes = True
