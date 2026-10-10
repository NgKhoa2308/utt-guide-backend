import math
from app.location.schemas import LocationResponseDTO, CreateLocationCommand, LocationFilter, CategoryCountResponse
from app.location.models import Location, LocationLike
from core.db import Transactional

class LocationNotFoundException(Exception):
    pass

class AlreadyLikedException(Exception):
    pass

CATEGORIES = [
    "Nhà trọ", "Quán ăn", "Cà phê", "Giải trí",
    "Thể thao", "Cửa hàng tiện lợi", "Khác"
]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Haversine formula
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class LocationService:
    def __init__(self, *, repository):
        self.repository = repository

    async def get_locations(self, *, filter: LocationFilter) -> list[LocationResponseDTO]:
        locations = await self.repository.get_locations(
            limit=filter.limit,
            offset=filter.offset,
            category=filter.category,
            min_price=filter.min_price,
            max_price=filter.max_price,
            keyword=filter.keyword,
            sort_by=filter.sort_by
        )
        
        if filter.lat is not None and filter.lng is not None and filter.radius is not None:
            # Filter by radius locally if coords are provided
            nearby = []
            for loc in locations:
                dist = calculate_distance(filter.lat, filter.lng, loc.lat, loc.lng)
                if dist <= filter.radius:
                    nearby.append(loc)
            locations = nearby
            
        if filter.sort_by == "distance" and filter.lat is not None and filter.lng is not None:
            locations = sorted(locations, key=lambda loc: calculate_distance(filter.lat, filter.lng, loc.lat, loc.lng))
            
        return [LocationResponseDTO.model_validate(loc) for loc in locations]

    async def get_featured(self, *, limit: int = 10) -> list[LocationResponseDTO]:
        locations = await self.repository.get_featured_locations(limit=limit)
        return [LocationResponseDTO.model_validate(loc) for loc in locations]

    @Transactional()
    async def get_by_id(self, *, location_id: int) -> LocationResponseDTO:
        location = await self.repository.get_by_id(location_id=location_id)
        if not location:
            raise LocationNotFoundException(f"Không tìm thấy địa điểm #{location_id}")
        await self.repository.increment_view_count(location_id=location_id)
        # We need to refresh or just manually increment for the DTO
        location.view_count += 1
        return LocationResponseDTO.model_validate(location)

    async def get_categories(self) -> list[CategoryCountResponse]:
        counts = await self.repository.get_category_counts()
        count_map = {category: count for category, count in counts}
        
        result = []
        for cat in CATEGORIES:
            result.append(CategoryCountResponse(category=cat, count=count_map.get(cat, 0)))
        return result

    @Transactional()
    async def submit_location(
        self, *, command: CreateLocationCommand, user_id: int
    ) -> LocationResponseDTO:
        location = Location.create(
            name=command.name,
            description=command.description,
            address=command.address,
            category=command.category,
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

    # PHASE 2 & 3 EXTENSIONS

    @Transactional()
    async def add_review(
        self, *, location_id: int, user_id: int, rating: int, content: str | None
    ) -> None:
        location = await self.repository.get_by_id(location_id=location_id)
        if not location:
            raise LocationNotFoundException("Địa điểm không tồn tại")
        
        review = LocationReview.create(
            location_id=location_id,
            user_id=user_id,
            rating=rating,
            content=content
        )
        await self.repository.add_review(review=review)

    async def get_reviews(self, *, location_id: int, limit: int = 10, offset: int = 0) -> list:
        # We will return list of LocationReview entities, caller maps to DTO
        return await self.repository.get_reviews_by_location(
            location_id=location_id, limit=limit, offset=offset
        )

    @Transactional()
    async def delete_review(self, *, review_id: int, user_id: int) -> None:
        review = await self.repository.get_review_by_id(review_id=review_id)
        if not review:
            raise Exception("Đánh giá không tồn tại")
        if review.user_id != user_id:
            raise Exception("Bạn không có quyền xóa đánh giá này")
        await self.repository.delete_review(review=review)

    async def get_favorites(self, *, user_id: int) -> list[LocationResponseDTO]:
        locations = await self.repository.get_user_favorites(user_id=user_id)
        return [LocationResponseDTO.model_validate(loc) for loc in locations]

    @Transactional()
    async def unlike_location(self, *, location_id: int, user_id: int) -> None:
        like = await self.repository.get_like(location_id=location_id, user_id=user_id)
        if not like:
            raise Exception("Bạn chưa thích địa điểm này")
        await self.repository.delete_like(like=like)

    async def get_stats(self) -> dict:
        stats = await self.repository.get_global_stats()
        return {
            "total_locations": stats["total_locations"],
            "total_categories": stats["total_categories"],
            "most_viewed": [LocationResponseDTO.model_validate(loc) for loc in stats["most_viewed"]]
        }

    @Transactional()
    async def update_location(self, *, location_id: int, **kwargs) -> LocationResponseDTO:
        location = await self.repository.get_by_id(location_id=location_id)
        if not location:
            raise LocationNotFoundException("Địa điểm không tồn tại")
            
        for key, value in kwargs.items():
            if value is not None:
                setattr(location, key, value)
                
        return LocationResponseDTO.model_validate(location)

    @Transactional()
    async def delete_location(self, *, location_id: int) -> None:
        location = await self.repository.get_by_id(location_id=location_id)
        if not location:
            raise LocationNotFoundException("Địa điểm không tồn tại")
        await self.repository.delete_location(location=location)
