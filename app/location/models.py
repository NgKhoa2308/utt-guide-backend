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
    min_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[LocationStatus] = mapped_column(
        Enum(LocationStatus), default=LocationStatus.PENDING
    )
    submitted_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )

    likes: Mapped[list["LocationLike"]] = relationship(
        "LocationLike", back_populates="location"
    )

    @property
    def like_count(self) -> int:
        return len(self.likes)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        lat: float,
        lng: float,
        submitted_by: int,
        description: str | None = None,
        photo_url: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
    ) -> "Location":
        return cls(
            name=name,
            description=description,
            lat=lat,
            lng=lng,
            submitted_by=submitted_by,
            photo_url=photo_url,
            min_price=min_price,
            max_price=max_price,
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
