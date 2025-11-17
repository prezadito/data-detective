"""
Marketing pages routes - server-side rendered pages for SEO and public content.
"""

import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
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

    # Analytics configuration
    analytics_enabled = os.getenv("ANALYTICS_ENABLED", "false").lower() == "true"
    analytics_provider = os.getenv("ANALYTICS_PROVIDER", "plausible")  # 'plausible' or 'google'

    # Plausible configuration
    analytics_domain = os.getenv("ANALYTICS_DOMAIN", "datadetective.academy")
    analytics_script_url = os.getenv(
        "ANALYTICS_SCRIPT_URL",
        "https://plausible.io/js/script.js"  # Use hosted Plausible or self-hosted URL
    )

    # Google Analytics configuration (if using GA instead)
    analytics_id = os.getenv("ANALYTICS_ID", "")  # e.g., G-XXXXXXXXXX for GA4

    return {
        "request": request,
        "app_name": "Data Detective Academy",
        "current_year": datetime.now().year,
        "frontend_url": frontend_url,
        "analytics_enabled": analytics_enabled,
        "analytics_provider": analytics_provider,
        "analytics_domain": analytics_domain,
        "analytics_script_url": analytics_script_url,
        "analytics_id": analytics_id,
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


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """
    About page - server-side rendered for SEO.

    Displays:
    - Mission statement
    - Company story and history
    - Team information
    - Core values
    - Open source commitment

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    # Build context
    context = get_base_context(request)

    return templates.TemplateResponse("about.html", context)


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """
    Contact page - server-side rendered for SEO.

    Displays:
    - Contact form for inquiries
    - Contact information (email, support)
    - FAQ section
    - Response time expectations

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    # Build context
    context = get_base_context(request)

    return templates.TemplateResponse("contact.html", context)


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """
    Privacy Policy page - server-side rendered for SEO.

    Displays:
    - Comprehensive privacy policy
    - Data collection and usage information
    - Student privacy and COPPA compliance
    - Data security measures
    - User rights and choices

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    # Build context
    context = get_base_context(request)

    return templates.TemplateResponse("privacy.html", context)


@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    """
    Terms of Service page - server-side rendered for SEO.

    Displays:
    - Terms of Service agreement
    - User rights and responsibilities
    - Acceptable use policy
    - AGPL-3.0 license information
    - Disclaimers and liability limitations

    Args:
        request: FastAPI request object

    Returns:
        Rendered HTML template
    """
    # Build context
    context = get_base_context(request)

    return templates.TemplateResponse("terms.html", context)


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """
    Robots.txt file for search engine crawlers.

    Returns:
        Plain text robots.txt content
    """
    robots_content = """# robots.txt for Data Detective Academy
# https://www.robotstxt.org/

# Allow all crawlers to access public content
User-agent: *
Allow: /
Allow: /features
Allow: /pricing
Allow: /about
Allow: /contact
Allow: /privacy
Allow: /terms

# Disallow access to API endpoints (should be accessed via frontend)
Disallow: /api/
Disallow: /auth/
Disallow: /users/
Disallow: /challenges/
Disallow: /progress/
Disallow: /leaderboard/
Disallow: /hints/
Disallow: /reports/
Disallow: /analytics/
Disallow: /export/
Disallow: /import/
Disallow: /datasets/

# Disallow access to static admin/internal files
Disallow: /static/admin/
Disallow: /.env
Disallow: /.git

# Crawl-delay for polite crawling
Crawl-delay: 1

# Sitemap location
Sitemap: {base_url}/sitemap.xml
"""
    # Get base URL from environment or use default
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    return robots_content.format(base_url=base_url)


@router.get("/sitemap.xml", response_class=Response)
async def sitemap_xml(request: Request):
    """
    Dynamic sitemap.xml generation for SEO.

    Generates a sitemap containing:
    - All marketing pages (home, features, pricing, about, contact, privacy, terms)
    - Last modification dates
    - Change frequency hints
    - Priority values

    Args:
        request: FastAPI request object

    Returns:
        XML sitemap content
    """
    # Get base URL from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # Define pages with their metadata
    pages = [
        {
            "loc": f"{base_url}/",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
            "changefreq": "daily",
            "priority": "1.0",
        },
        {
            "loc": f"{base_url}/features",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
            "changefreq": "weekly",
            "priority": "0.9",
        },
        {
            "loc": f"{base_url}/pricing",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
            "changefreq": "weekly",
            "priority": "0.9",
        },
        {
            "loc": f"{base_url}/about",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
            "changefreq": "monthly",
            "priority": "0.7",
        },
        {
            "loc": f"{base_url}/contact",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
            "changefreq": "monthly",
            "priority": "0.6",
        },
        {
            "loc": f"{base_url}/privacy",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
            "changefreq": "monthly",
            "priority": "0.5",
        },
        {
            "loc": f"{base_url}/terms",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
            "changefreq": "monthly",
            "priority": "0.5",
        },
    ]

    # Build sitemap XML
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for page in pages:
        sitemap_xml += "  <url>\n"
        sitemap_xml += f"    <loc>{page['loc']}</loc>\n"
        sitemap_xml += f"    <lastmod>{page['lastmod']}</lastmod>\n"
        sitemap_xml += f"    <changefreq>{page['changefreq']}</changefreq>\n"
        sitemap_xml += f"    <priority>{page['priority']}</priority>\n"
        sitemap_xml += "  </url>\n"

    sitemap_xml += "</urlset>"

    return Response(content=sitemap_xml, media_type="application/xml")
