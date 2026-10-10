from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Path, Request
from fastapi.responses import JSONResponse

from app.container import Container
from app.location.service import (
    LocationService,
    LocationNotFoundException,
    AlreadyLikedException,
)
from app.location.schemas import CreateLocationCommand, LocationFilter
from core.fastapi.dependencies import IsAuthenticated, IsAdmin, PermissionDependency

location_router = APIRouter()

@location_router.get("")
@inject
async def get_locations(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    min_price: int | None = Query(None),
    max_price: int | None = Query(None),
    keyword: str | None = Query(None),
    sort_by: str | None = Query(None, description="price_asc, price_desc, name, distance"),
    lat: float | None = Query(None, description="Current latitude for distance sorting/filtering"),
    lng: float | None = Query(None, description="Current longitude for distance sorting/filtering"),
    radius: float | None = Query(None, description="Radius in km"),
    service: LocationService = Depends(Provide[Container.location_service]),
):
    filter = LocationFilter(
        limit=limit,
        offset=offset,
        category=category,
        min_price=min_price,
        max_price=max_price,
        keyword=keyword,
        sort_by=sort_by,
        lat=lat,
        lng=lng,
        radius=radius
    )
    return await service.get_locations(filter=filter)

@location_router.get("/categories")
@inject
async def get_categories(
    service: LocationService = Depends(Provide[Container.location_service]),
):
    return await service.get_categories()

@location_router.get("/featured")
@inject
async def get_featured_locations(
    limit: int = Query(10),
    service: LocationService = Depends(Provide[Container.location_service]),
):
    return await service.get_featured(limit=limit)

@location_router.get("/{location_id}")
@inject
async def get_location_by_id(
    location_id: int = Path(...),
    service: LocationService = Depends(Provide[Container.location_service]),
):
    try:
        return await service.get_by_id(location_id=location_id)
    except LocationNotFoundException as e:
        return JSONResponse(status_code=404, content={"message": str(e)})

@location_router.post(
    "",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
@inject
async def submit_location(
    request: Request,
    command: CreateLocationCommand,
    service: LocationService = Depends(Provide[Container.location_service]),
):
    return await service.submit_location(command=command, user_id=request.user.id)

@location_router.patch(
    "/{location_id}/approve",
    dependencies=[Depends(PermissionDependency([IsAdmin]))],
)
@inject
async def approve_location(
    location_id: int = Path(...),
    service: LocationService = Depends(Provide[Container.location_service]),
):
    try:
        await service.approve_location(location_id=location_id)
        return {"message": "Đã duyệt thành công"}
    except LocationNotFoundException as e:
        return JSONResponse(status_code=404, content={"message": str(e)})

@location_router.post(
    "/{location_id}/like",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
@inject
async def like_location(
    request: Request,
    location_id: int = Path(...),
    service: LocationService = Depends(Provide[Container.location_service]),
):
    try:
        await service.like_location(location_id=location_id, user_id=request.user.id)
        return {"message": "Đã thích địa điểm"}
    except AlreadyLikedException as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
