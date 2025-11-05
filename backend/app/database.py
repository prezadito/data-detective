"""
Database configuration and session management
"""

from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
from app.models import User  # noqa: F401

# Database URL (SQLite for development)
DATABASE_URL = "sqlite:///./data_detective_academy.db"

# Create engine
# check_same_thread=False is only needed for SQLite
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Print SQL queries (helpful for learning!)
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    """
    Create all database tables
    Called once at the application startup
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session
    Automatically closes session after use

    Yields:
        Session: Database Session
    """
    with Session(engine) as session:
        yield session
