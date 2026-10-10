from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from dependency_injector.providers import Factory, Singleton

from app.auth.application.service.jwt import JwtService
from app.user.adapter.output.persistence.repository_adapter import UserRepositoryAdapter
from app.user.adapter.output.persistence.sqlalchemy.user import UserSQLAlchemyRepo
from app.user.application.service.user import UserService

from app.location.repository import LocationRepository
from app.location.service import LocationService


class Container(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=["app"], modules=["app.location.router"])

    user_repo = Singleton(UserSQLAlchemyRepo)
    user_repo_adapter = Factory(UserRepositoryAdapter, user_repo=user_repo)
    user_service = Factory(UserService, repository=user_repo_adapter)

    jwt_service = Factory(JwtService)

    location_repo = Singleton(LocationRepository)
    location_service = Factory(LocationService, repository=location_repo)
