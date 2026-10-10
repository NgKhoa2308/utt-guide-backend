from enum import Enum as PyEnum

from sqlalchemy import String, Text, Float, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.db.mixins import TimestampMixin

class LocationStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Location(Base, TimestampMixin):
    __tablename__ = "location"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Khác")
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    min_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[LocationStatus] = mapped_column(
        Enum(LocationStatus), default=LocationStatus.PENDING
    )
    submitted_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )

    likes: Mapped[list["LocationLike"]] = relationship(
        "LocationLike", back_populates="location"
    )
    reviews: Mapped[list["LocationReview"]] = relationship(
        "LocationReview", back_populates="location"
    )

    @property
    def like_count(self) -> int:
        return len(self.likes)

    @property
    def review_count(self) -> int:
        return len(self.reviews)

    @property
    def average_rating(self) -> float:
        if not self.reviews:
            return 0.0
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        lat: float,
        lng: float,
        category: str,
        submitted_by: int,
        address: str | None = None,
        description: str | None = None,
        photo_url: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
    ) -> "Location":
        return cls(
            name=name,
            description=description,
            address=address,
            lat=lat,
            lng=lng,
            category=category,
            submitted_by=submitted_by,
            photo_url=photo_url,
            min_price=min_price,
            max_price=max_price,
            view_count=0,
            status=LocationStatus.PENDING,
        )

class LocationLike(Base, TimestampMixin):
    __tablename__ = "location_like"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("location.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )

    location: Mapped["Location"] = relationship(
        "Location", back_populates="likes"
    )

class LocationReview(Base, TimestampMixin):
    __tablename__ = "location_review"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("location.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False) # 1 to 5
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped["Location"] = relationship(
        "Location", back_populates="reviews"
    )

    @classmethod
    def create(
        cls,
        *,
        location_id: int,
        user_id: int,
        rating: int,
        content: str | None = None,
    ) -> "LocationReview":
        return cls(
            location_id=location_id,
            user_id=user_id,
            rating=rating,
            content=content,
        )
