"""
Marketing pages routes - server-side rendered pages for SEO and public content.
"""

import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, Progress
from app.challenges import CHALLENGES

# Initialize Jinja2 templates
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

# Router with no prefix (serves root paths)
router = APIRouter(tags=["Marketing"])


def get_base_context(request: Request, **kwargs) -> dict:
    """
    Build base context for all marketing templates.

    Args:
        request: FastAPI request object (required by Jinja2Templates)
        **kwargs: Additional context variables to merge

    Returns:
        Dictionary with base context variables
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    return {
        "request": request,
        "app_name": "Data Detective Academy",
        "current_year": datetime.now().year,
        "frontend_url": frontend_url,
        **kwargs,  # Merge page-specific context
    }


def get_platform_stats(session: Session) -> dict:
    """
    Get platform statistics for the homepage.

    Args:
        session: Database session

    Returns:
        Dictionary with stats (total_students, total_challenges, etc.)
    """
    # Count total students
    total_students = (
        session.exec(
            select(func.count(func.distinct(User.id))).where(User.role == "student")
        ).one()
        or 0
    )

    # Total number of challenges (from hardcoded CHALLENGES dict)
    total_challenges = len(CHALLENGES)

    # Count total completed challenges (submissions)
    total_submissions = (
        session.exec(select(func.count(Progress.id))).one() or 0
    )

    # Calculate success rate (challenges with at least one completion / total challenges)
    if total_challenges > 0:
        completed_challenges = (
            session.exec(
                select(func.count(func.distinct(Progress.challenge_id)))
            ).one()
            or 0
        )
        success_rate = round((completed_challenges / total_challenges) * 100)
    else:
        success_rate = 0

    return {
        "total_students": total_students,
        "total_challenges": total_challenges,
        "total_submissions": total_submissions,
        "success_rate": success_rate,
    }


# ============================================================================
# ROUTES
# ============================================================================


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    """
    Home/Landing page - server-side rendered for SEO.

    Displays:
    - Hero section with value proposition
    - Platform statistics
    - Features overview
    - How it works
    - Curriculum overview
    - Testimonials
    - CTA sections

    Args:
        request: FastAPI request object
        session: Database session (for stats)

    Returns:
        Rendered HTML template
    """
    # Get platform statistics
    stats = get_platform_stats(session)

    # Build context
    context = get_base_context(
        request,
        stats=stats,
    )

    return templates.TemplateResponse("landing.html", context)


@router.get("/features", response_class=HTMLResponse)
async def features(request: Request):
    """
    Features page - server-side rendered for SEO.

    Displays:
    - Comprehensive feature descriptions with icons
    - Screenshots/mockups of the platform
    - Student benefits section
    - Teacher benefits section
    - Feature comparison table
    - CTA linking to pricing page

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    # Build context
    context = get_base_context(request)

    return templates.TemplateResponse("features.html", context)


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """
    Pricing page - server-side rendered for SEO.

    Displays:
    - Three pricing tiers: Freedom Edition, School, and District
    - Detailed feature comparison matrix
    - FAQ section answering common pricing questions
    - Contact sales CTA for enterprise customers

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    # Build context
    context = get_base_context(request)

    return templates.TemplateResponse("pricing.html", context)
