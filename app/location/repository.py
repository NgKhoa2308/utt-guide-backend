from sqlalchemy import select, update, func, or_
from sqlalchemy.orm import selectinload

from app.location.models import Location, LocationLike, LocationStatus, LocationReview
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

    # PHASE 2 & 3 EXTENSIONS
    
    async def add_review(self, *, review: LocationReview) -> None:
        session.add(review)

    async def get_reviews_by_location(self, *, location_id: int, limit: int, offset: int) -> list[LocationReview]:
        query = (
            select(LocationReview)
            .where(LocationReview.location_id == location_id)
            .order_by(LocationReview.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_review_by_id(self, *, review_id: int) -> LocationReview | None:
        query = select(LocationReview).where(LocationReview.id == review_id)
        result = await session.execute(query)
        return result.scalars().first()

    async def delete_review(self, *, review: LocationReview) -> None:
        await session.delete(review)

    async def get_user_favorites(self, *, user_id: int) -> list[Location]:
        query = (
            select(Location)
            .join(LocationLike, Location.id == LocationLike.location_id)
            .where(LocationLike.user_id == user_id)
            .options(selectinload(Location.likes), selectinload(Location.reviews))
        )
        result = await session.execute(query)
        return list(result.scalars().all())
        
    async def delete_like(self, *, like: LocationLike) -> None:
        await session.delete(like)

    async def get_global_stats(self) -> dict:
        total_loc = await session.scalar(select(func.count(Location.id)).where(Location.status == LocationStatus.APPROVED))
        total_cat = await session.scalar(select(func.count(Location.category.distinct())).where(Location.status == LocationStatus.APPROVED))
        
        most_viewed_query = (
            select(Location)
            .where(Location.status == LocationStatus.APPROVED)
            .options(selectinload(Location.likes), selectinload(Location.reviews))
            .order_by(Location.view_count.desc())
            .limit(5)
        )
        most_viewed = list((await session.execute(most_viewed_query)).scalars().all())
        
        return {
            "total_locations": total_loc or 0,
            "total_categories": total_cat or 0,
            "most_viewed": most_viewed
        }
        
    async def delete_location(self, *, location: Location) -> None:
        await session.delete(location)
