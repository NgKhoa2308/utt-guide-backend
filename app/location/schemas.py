from pydantic import BaseModel
from app.location.models import LocationStatus

class CreateLocationCommand(BaseModel):
    name: str
    description: str | None = None
    address: str | None = None
    category: str
    lat: float
    lng: float
    photo_url: str | None = None
    min_price: int | None = None
    max_price: int | None = None

class LocationResponseDTO(BaseModel):
    id: int
    name: str
    description: str | None
    address: str | None
    category: str
    photo_url: str | None
    lat: float
    lng: float
    min_price: int | None
    max_price: int | None
    status: LocationStatus
    view_count: int
    like_count: int
    review_count: int
    average_rating: float

    class Config:
        from_attributes = True

class CategoryCountResponse(BaseModel):
    category: str
    count: int

class LocationFilter(BaseModel):
    limit: int = 10
    offset: int = 0
    category: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    keyword: str | None = None
    sort_by: str | None = None # "price_asc", "price_desc", "name", "distance"
    lat: float | None = None
    lng: float | None = None
    radius: float | None = None

from datetime import datetime

class ReviewCreateCommand(BaseModel):
    rating: int # 1 to 5
    content: str | None = None

class ReviewResponseDTO(BaseModel):
    id: int
    location_id: int
    user_id: int
    rating: int
    content: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class StatsResponseDTO(BaseModel):
    total_locations: int
    total_categories: int
    most_viewed: list[LocationResponseDTO]

class UpdateLocationCommand(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None
    category: str | None = None
    lat: float | None = None
    lng: float | None = None
    photo_url: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    status: LocationStatus | None = None
