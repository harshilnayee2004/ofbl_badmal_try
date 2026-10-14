from typing import Generator
from sqlmodel import Session, create_engine, SQLModel
from core.config import settings

connect_args = {"check_same_thread": False} if settings.USE_SQLITE else {}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session