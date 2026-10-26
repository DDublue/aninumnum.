from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import settings


engine = create_engine(
    url=settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool if settings.database_url == "sqlite://" else None, # for testing
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
