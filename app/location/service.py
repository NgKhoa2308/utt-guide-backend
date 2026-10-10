from app.location.schemas import LocationResponseDTO, CreateLocationCommand
from app.location.models import Location, LocationLike
from core.db import Transactional

class LocationNotFoundException(Exception):
    pass

class AlreadyLikedException(Exception):
    pass

class LocationService:
    def __init__(self, *, repository):
        self.repository = repository

    async def get_featured(self, *, limit: int = 10) -> list[LocationResponseDTO]:
        locations = await self.repository.get_featured_locations(limit=limit)
        return [LocationResponseDTO.model_validate(loc) for loc in locations]

    @Transactional()
    async def submit_location(
        self, *, command: CreateLocationCommand, user_id: int
    ) -> LocationResponseDTO:
        location = Location.create(
            name=command.name,
            description=command.description,
            lat=command.lat,
            lng=command.lng,
            submitted_by=user_id,
            photo_url=command.photo_url,
            min_price=command.min_price,
            max_price=command.max_price,
        )
        await self.repository.save(location=location)
        return LocationResponseDTO.model_validate(location)

    @Transactional()
    async def approve_location(self, *, location_id: int) -> None:
        location = await self.repository.get_by_id(location_id=location_id)
        if not location:
            raise LocationNotFoundException(f"Không tìm thấy địa điểm #{location_id}")
        await self.repository.approve(location_id=location_id)

    @Transactional()
    async def like_location(self, *, location_id: int, user_id: int) -> None:
        existing = await self.repository.get_like(
            location_id=location_id, user_id=user_id
        )
        if existing:
            raise AlreadyLikedException("Bạn đã thích địa điểm này rồi")

        like = LocationLike(location_id=location_id, user_id=user_id)
        await self.repository.save_like(like=like)
