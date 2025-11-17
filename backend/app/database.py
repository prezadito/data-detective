"""
Database configuration and session management
"""

from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
import os
from dotenv import load_dotenv
from app.models import (  # noqa: F401
    User,
    RefreshToken,
    PasswordResetToken,
    Progress,
    Hint,
    Attempt,
    Dataset,
    CustomChallenge,
)

# Load environment variables from .env file
load_dotenv()

# Database URL from environment variable (defaults to SQLite for development)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data_detective_academy.db")

# Database configuration from environment variables
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

# Determine database type
is_sqlite = DATABASE_URL.startswith("sqlite:")

# Create engine with appropriate configuration for database type
if is_sqlite:
    # SQLite configuration (development only)
    # check_same_thread=False allows SQLite to be used with FastAPI's async workers
    engine = create_engine(
        DATABASE_URL,
        echo=DB_ECHO,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL configuration (production)
    # pool_pre_ping=True: Verify connections are alive before using them
    # pool_size: Number of persistent connections in the pool
    # max_overflow: Additional connections that can be created when pool is full
    engine = create_engine(
        DATABASE_URL,
        echo=DB_ECHO,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Test connections before using
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
