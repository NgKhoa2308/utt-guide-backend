from sqlalchemy import select, update, func, or_
from sqlalchemy.orm import selectinload

from app.location.models import Location, LocationLike, LocationStatus
from core.db.session import session

class LocationRepository:
    async def get_featured_locations(self, *, limit: int) -> list[Location]:
        query = (
            select(Location)
            .where(Location.status == LocationStatus.APPROVED)
            .options(selectinload(Location.likes), selectinload(Location.reviews))
            .limit(limit)
        )
        result = await session.execute(query)
        locations = list(result.scalars().all())
        return sorted(locations, key=lambda loc: len(loc.likes), reverse=True)

    async def save(self, *, location: Location) -> None:
        session.add(location)

    async def get_by_id(self, *, location_id: int) -> Location | None:
        query = (
            select(Location)
            .options(selectinload(Location.likes), selectinload(Location.reviews))
            .where(Location.id == location_id)
        )
        result = await session.execute(query)
        return result.scalars().first()

    async def increment_view_count(self, *, location_id: int) -> None:
        query = (
            update(Location)
            .where(Location.id == location_id)
            .values(view_count=Location.view_count + 1)
        )
        await session.execute(query)

    async def get_locations(
        self,
        *,
        limit: int,
        offset: int,
        category: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        keyword: str | None = None,
        sort_by: str | None = None
    ) -> list[Location]:
        query = select(Location).where(Location.status == LocationStatus.APPROVED).options(selectinload(Location.likes), selectinload(Location.reviews))
        
        if category:
            query = query.where(Location.category == category)
        if min_price is not None:
            query = query.where(Location.max_price >= min_price)
        if max_price is not None:
            query = query.where(Location.min_price <= max_price)
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    Location.name.ilike(keyword_pattern),
                    Location.description.ilike(keyword_pattern),
                    Location.address.ilike(keyword_pattern)
                )
            )
            
        if sort_by == "price_asc":
            query = query.order_by(Location.min_price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Location.min_price.desc())
        elif sort_by == "name":
            query = query.order_by(Location.name.asc())
        else:
            query = query.order_by(Location.id.desc())
            
        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_category_counts(self) -> list[tuple[str, int]]:
        query = (
            select(Location.category, func.count(Location.id))
            .where(Location.status == LocationStatus.APPROVED)
            .group_by(Location.category)
        )
        result = await session.execute(query)
        return list(result.all())

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
