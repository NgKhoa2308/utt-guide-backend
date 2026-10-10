from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.location.models import Location, LocationLike, LocationStatus
from core.db.session import session

class LocationRepository:
    async def get_featured_locations(self, *, limit: int) -> list[Location]:
        query = (
            select(Location)
            .where(Location.status == LocationStatus.APPROVED)
            .options(selectinload(Location.likes))
            .limit(limit)
        )
        result = await session.execute(query)
        locations = list(result.scalars().all())
        return sorted(locations, key=lambda loc: len(loc.likes), reverse=True)

    async def save(self, *, location: Location) -> None:
        session.add(location)

    async def get_by_id(self, *, location_id: int) -> Location | None:
        query = select(Location).where(Location.id == location_id)
        result = await session.execute(query)
        return result.scalars().first()

    async def approve(self, *, location_id: int) -> None:
        query = (
            update(Location)
            .where(Location.id == location_id)
            .values(status=LocationStatus.APPROVED)
        )
        await session.execute(query)

    async def save_like(self, *, like: LocationLike) -> None:
        session.add(like)

    async def get_like(self, *, location_id: int, user_id: int) -> LocationLike | None:
        query = select(LocationLike).where(
            LocationLike.location_id == location_id,
            LocationLike.user_id == user_id,
        )
        result = await session.execute(query)
        return result.scalars().first()
