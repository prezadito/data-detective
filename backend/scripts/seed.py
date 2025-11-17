#!/usr/bin/env python3
"""
Seed script for Data Detective Academy database.

This script populates the database with sample data for development and testing:
- Teacher account
- Student accounts
- Sample progress data

Usage:
    uv run python scripts/seed.py [--clear] [--minimal]

Options:
    --clear     Clear all existing data before seeding (DESTRUCTIVE!)
    --minimal   Only create essential accounts (1 teacher, 2 students)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.database import engine, SQLModel
from app.models import User, Progress, Attempt, Hint
from app.auth import hash_password


# Sample data configuration
TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASSWORD = "teacher123"
TEACHER_NAME = "Ms. Johnson"

STUDENTS = [
    {"email": "alice@example.com", "password": "student123", "name": "Alice Cooper"},
    {"email": "bob@example.com", "password": "student123", "name": "Bob Smith"},
    {"email": "charlie@example.com", "password": "student123", "name": "Charlie Davis"},
    {
        "email": "diana@example.com",
        "password": "student123",
        "name": "Diana Martinez",
    },
    {"email": "eve@example.com", "password": "student123", "name": "Eve Thompson"},
]

# Sample progress data (challenge completions)
SAMPLE_PROGRESS = [
    # Alice completed Unit 1, Challenge 1 and 2
    {
        "email": "alice@example.com",
        "unit_id": 1,
        "challenge_id": 1,
        "points_earned": 100,
        "hints_used": 0,
        "query": "SELECT * FROM users",
    },
    {
        "email": "alice@example.com",
        "unit_id": 1,
        "challenge_id": 2,
        "points_earned": 100,
        "hints_used": 1,
        "query": "SELECT name, email FROM users",
    },
    # Bob completed Unit 1, Challenge 1
    {
        "email": "bob@example.com",
        "unit_id": 1,
        "challenge_id": 1,
        "points_earned": 75,
        "hints_used": 2,
        "query": "SELECT * FROM users",
    },
]


def clear_all_data(session: Session) -> None:
    """
    Clear all data from the database.

    WARNING: This is DESTRUCTIVE and will delete all data!

    Args:
        session: Database session
    """
    print("⚠️  Clearing all existing data...")

    # Delete in reverse dependency order
    session.query(Progress).delete()
    session.query(Attempt).delete()
    session.query(Hint).delete()
    session.query(User).delete()

    session.commit()
    print("✅ All data cleared")


def create_teacher(session: Session) -> User:
    """
    Create or get the default teacher account.

    Args:
        session: Database session

    Returns:
        Teacher user object
    """
    # Check if teacher already exists
    statement = select(User).where(User.email == TEACHER_EMAIL)
    teacher = session.exec(statement).first()

    if teacher:
        print(f"ℹ️  Teacher account already exists: {TEACHER_EMAIL}")
        return teacher

    # Create teacher
    teacher = User(
        email=TEACHER_EMAIL,
        name=TEACHER_NAME,
        role="teacher",
        password_hash=hash_password(TEACHER_PASSWORD),
        created_at=datetime.now(timezone.utc),
    )

    session.add(teacher)
    session.commit()
    session.refresh(teacher)

    print(f"✅ Created teacher account: {TEACHER_EMAIL}")
    print(f"   Password: {TEACHER_PASSWORD}")

    return teacher


def create_students(session: Session, minimal: bool = False) -> list[User]:
    """
    Create sample student accounts.

    Args:
        session: Database session
        minimal: If True, only create 2 students instead of all

    Returns:
        List of student user objects
    """
    students_to_create = STUDENTS[:2] if minimal else STUDENTS
    created_students = []

    for student_data in students_to_create:
        # Check if student already exists
        statement = select(User).where(User.email == student_data["email"])
        student = session.exec(statement).first()

        if student:
            print(f"ℹ️  Student already exists: {student_data['email']}")
            created_students.append(student)
            continue

        # Create student
        student = User(
            email=student_data["email"],
            name=student_data["name"],
            role="student",
            password_hash=hash_password(student_data["password"]),
            created_at=datetime.now(timezone.utc),
        )

        session.add(student)
        session.commit()
        session.refresh(student)

        print(f"✅ Created student account: {student_data['email']}")
        print(f"   Password: {student_data['password']}")

        created_students.append(student)

    return created_students


def create_sample_progress(session: Session) -> None:
    """
    Create sample progress data for students.

    Args:
        session: Database session
    """
    for progress_data in SAMPLE_PROGRESS:
        # Get student by email
        statement = select(User).where(User.email == progress_data["email"])
        student = session.exec(statement).first()

        if not student:
            print(f"⚠️  Student not found: {progress_data['email']}")
            continue

        # Check if progress already exists
        progress_statement = select(Progress).where(
            Progress.user_id == student.id,
            Progress.unit_id == progress_data["unit_id"],
            Progress.challenge_id == progress_data["challenge_id"],
        )
        existing_progress = session.exec(progress_statement).first()

        if existing_progress:
            print(
                f"ℹ️  Progress already exists for {progress_data['email']} - "
                f"Unit {progress_data['unit_id']}, Challenge {progress_data['challenge_id']}"
            )
            continue

        # Create progress
        progress = Progress(
            user_id=student.id,
            unit_id=progress_data["unit_id"],
            challenge_id=progress_data["challenge_id"],
            points_earned=progress_data["points_earned"],
            hints_used=progress_data["hints_used"],
            query=progress_data["query"],
            completed_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        session.add(progress)
        session.commit()

        print(
            f"✅ Created progress for {progress_data['email']} - "
            f"Unit {progress_data['unit_id']}, Challenge {progress_data['challenge_id']}"
        )


def seed_database(clear: bool = False, minimal: bool = False) -> None:
    """
    Main seeding function.

    Args:
        clear: If True, clear all existing data first
        minimal: If True, only create minimal data set
    """
    print("🌱 Starting database seeding...")
    print(f"   Mode: {'MINIMAL' if minimal else 'FULL'}")
    print(f"   Clear existing data: {clear}")
    print()

    with Session(engine) as session:
        # Clear data if requested
        if clear:
            clear_all_data(session)
            print()

        # Create teacher
        teacher = create_teacher(session)
        print()

        # Create students
        students = create_students(session, minimal=minimal)
        print()

        # Create sample progress (only in full mode)
        if not minimal:
            create_sample_progress(session)
            print()

    print("✅ Database seeding completed!")
    print()
    print("📋 Summary:")
    print(f"   Teacher: {TEACHER_EMAIL} / {TEACHER_PASSWORD}")
    print(f"   Students: {len(students)} accounts created")
    print()
    print("🔗 You can now log in at http://localhost:3000")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed the Data Detective Academy database"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all existing data before seeding (DESTRUCTIVE!)",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Only create essential accounts (1 teacher, 2 students)",
    )

    args = parser.parse_args()

    # Confirm before clearing
    if args.clear:
        print("⚠️  WARNING: You are about to DELETE ALL DATA from the database!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    try:
        seed_database(clear=args.clear, minimal=args.minimal)
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
