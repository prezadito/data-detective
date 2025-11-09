"""
Database configuration and session management
"""

from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
import os
from dotenv import load_dotenv
from app.models import User, RefreshToken, PasswordResetToken  # noqa: F401

# Load environment variables from .env file
load_dotenv()

# Database URL from environment variable (defaults to SQLite for development)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data_detective_academy.db")

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
