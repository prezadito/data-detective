# 🔍 Data Detective Academy

<div align="center">

**A gamified SQL education platform for grades 4-8**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://reactjs.org/)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

**Data Detective Academy** is an interactive SQL learning platform designed to make database education engaging and accessible for middle school students. Through gamification, real-time feedback, and progress tracking, students learn SQL fundamentals while teachers gain powerful analytics and classroom management tools.

### 🎯 Key Features

#### For Students
- **Interactive SQL Challenges** - 7 progressively challenging SQL exercises across 3 units
- **Real-time Query Validation** - Instant feedback on SQL submissions
- **Gamification** - Earn points, track progress, and compete on leaderboards
- **Hint System** - Multi-level hints to guide learning without giving away solutions
- **Progress Tracking** - Visualize your learning journey with detailed statistics
- **Achievement System** - Unlock badges and milestones as you master SQL

#### For Teachers
- **Student Management** - View, search, and manage student accounts
- **Class Analytics** - Comprehensive dashboards showing class-wide performance
- **Progress Monitoring** - Track individual student progress and completion rates
- **Bulk Import** - CSV-based student roster import for easy class setup
- **Data Export** - Export student data and progress reports
- **Weekly Reports** - Automated progress summaries for each student

### 🏗️ Architecture

This is a full-stack monorepo application:

```
data-detective/
├── backend/          # FastAPI REST API (Python 3.13+)
├── frontend/         # React + TypeScript UI (Vite)
├── docs/            # Comprehensive documentation
└── scripts/         # Development helper scripts
```

**Tech Stack:**
- **Backend**: FastAPI, SQLModel, SQLite/PostgreSQL, JWT Auth
- **Frontend**: React 19, TypeScript, Tailwind CSS, Vite
- **Testing**: Pytest (backend), Vitest + Playwright (frontend)
- **Package Managers**: uv (backend), pnpm (frontend)

---

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.13+, uv package manager
- **Frontend**: Node.js 18+, pnpm
- **Database**: SQLite (dev) or PostgreSQL (production)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd data-detective
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync --all-extras

# Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY (generate: openssl rand -hex 32)

# Run tests
uv run pytest tests/ -v

# Start server (http://localhost:8000)
uvicorn app.main:app --reload
```

**API Documentation:** http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Configure environment
cp .env.example .env
# Edit .env if needed (defaults to http://localhost:8000)

# Run tests
pnpm test

# Start dev server (http://localhost:3000)
pnpm dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000

**Default Test Users:**
- Student: `e2e-student@test.com` / `Test123!`
- Teacher: `e2e-teacher@test.com` / `Test123!`

---

## 📚 Documentation

### General Documentation
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design, data flow, and technical decisions
- **[API Reference](docs/API.md)** - Complete API documentation with examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Component Documentation
- **[Frontend Components](docs/COMPONENTS.md)** - React component library reference
- **[Frontend README](frontend/README.md)** - Frontend development guide
- **[Backend README](backend/README.md)** - Backend development guide

### AI Assistant Documentation
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive guide for AI assistants
- **[Backend CLAUDE.md](backend/CLAUDE.md)** - Backend-specific AI guide

---

## 🛠️ Development

### Available Scripts

#### Backend
```bash
cd backend

# Development
uvicorn app.main:app --reload    # Start dev server
uv run pytest tests/ -v          # Run tests
uv run pytest --cov=app          # Tests with coverage

# Code Quality
uv run ruff check .              # Lint
uv run ruff check . --fix        # Auto-fix linting issues
uv run ruff format .             # Format code

# Database
uv run sqlite_web data_detective_academy.db  # Browse database
```

#### Frontend
```bash
cd frontend

# Development
pnpm dev                         # Start dev server
pnpm build                       # Build for production
pnpm preview                     # Preview production build

# Testing
pnpm test                        # Run unit tests
pnpm test:ui                     # Run tests with UI
pnpm test:coverage               # Tests with coverage
pnpm test:e2e                    # Run E2E tests (requires backend)
pnpm test:e2e:ui                 # E2E tests with UI

# Code Quality
pnpm lint                        # Lint code
pnpm exec tsc --noEmit           # Type check
```

### Project Structure

#### Backend Structure
```
backend/
├── app/
│   ├── routes/          # API endpoints (13 routers)
│   │   ├── auth.py              # Authentication
│   │   ├── users.py             # User management
│   │   ├── challenges.py        # Challenge browsing
│   │   ├── progress.py          # Progress tracking
│   │   ├── leaderboard.py       # Leaderboard
│   │   ├── analytics.py         # Teacher analytics
│   │   ├── export.py            # Data export
│   │   ├── bulk_import.py       # CSV student import
│   │   ├── hints.py             # Hint system
│   │   ├── reports.py           # Weekly reports
│   │   ├── custom_challenges.py # Custom challenges
│   │   └── datasets.py          # Dataset management
│   ├── models.py        # Database models (6 tables)
│   ├── schemas.py       # Pydantic schemas (58 schemas)
│   ├── auth.py          # Auth utilities
│   ├── database.py      # DB configuration
│   ├── challenges.py    # Challenge definitions
│   └── main.py          # Application entry point
├── tests/               # Pytest test suite (18 files)
└── pyproject.toml       # Dependencies & config
```

#### Frontend Structure
```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── auth/            # Login, Register
│   │   ├── challenge/       # Challenge UI
│   │   ├── leaderboard/     # Leaderboard table
│   │   ├── navigation/      # Navigation bar
│   │   ├── progress/        # Progress tracking
│   │   ├── query/           # SQL query editor
│   │   ├── routing/         # Protected routes
│   │   ├── teacher/         # Teacher dashboard
│   │   └── ui/              # Reusable UI components
│   ├── pages/           # Page components
│   ├── contexts/        # React contexts (AuthContext)
│   ├── services/        # API service layer
│   ├── hooks/           # Custom hooks
│   ├── types/           # TypeScript types
│   └── utils/           # Utility functions
├── tests/
│   ├── e2e/            # Playwright E2E tests
│   └── unit/           # Vitest unit tests
└── package.json        # Dependencies & scripts
```

---

## 🎓 Learning SQL with Data Detective

### Challenge Units

**Unit 1: SELECT Basics** (3 challenges)
- SELECT all columns
- SELECT specific columns
- WHERE clause filtering

**Unit 2: JOINs** (2 challenges)
- INNER JOIN basics
- Multiple table joins

**Unit 3: Aggregations** (2 challenges)
- COUNT, SUM, AVG functions
- GROUP BY and HAVING

### How It Works

1. **Choose a Challenge** - Browse available SQL challenges
2. **Write SQL** - Use the interactive query editor
3. **Submit & Validate** - Get instant feedback on your solution
4. **Earn Points** - Successful solutions earn points (with penalties for hints)
5. **Track Progress** - View your statistics and achievements
6. **Compete** - Climb the leaderboard

---

## 🧪 Testing

### Backend Testing
```bash
cd backend
uv run pytest tests/ -v              # All tests
uv run pytest tests/test_auth.py -v  # Specific test file
uv run pytest --cov=app              # With coverage
```

- 18 test files with comprehensive coverage
- In-memory SQLite for fast testing
- Async test support with pytest-asyncio

### Frontend Testing

**Unit Tests (Vitest)**
```bash
cd frontend
pnpm test                # Run all unit tests
pnpm test:ui             # Interactive test UI
pnpm test:coverage       # Coverage report
```

**E2E Tests (Playwright)**
```bash
pnpm test:e2e           # Headless mode
pnpm test:e2e:ui        # Interactive mode
pnpm test:e2e:headed    # See browser
pnpm test:e2e:debug     # Debug mode
```

- Multi-browser testing (Chromium, Firefox)
- Student and teacher user journey tests
- Automatic screenshots/videos on failure

---

## 🚢 Deployment

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for comprehensive deployment instructions.

### Quick Deployment Overview

**Backend Deployment Options:**
- Docker container
- Traditional Python server (Gunicorn + Uvicorn)
- Cloud platforms (AWS, GCP, Azure)

**Frontend Deployment Options:**
- Static hosting (Netlify, Vercel, Cloudflare Pages)
- Traditional web server (Nginx, Apache)
- CDN deployment

**Database:**
- Development: SQLite
- Production: PostgreSQL (recommended)

---

## 🤝 Contributing

We welcome contributions! Please see our **[Contributing Guide](docs/CONTRIBUTING.md)** for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Checklist

Before submitting a PR:

**Backend:**
- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] No linting errors (`uv run ruff check .`)
- [ ] Code formatted (`uv run ruff format .`)
- [ ] Type hints on all functions

**Frontend:**
- [ ] All tests pass (`pnpm test`)
- [ ] No type errors (`pnpm exec tsc --noEmit`)
- [ ] No linting errors (`pnpm lint`)
- [ ] E2E tests pass (`pnpm test:e2e`)

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

See [LICENSE](LICENSE) for details.

**Key Points:**
- Free to use, modify, and distribute
- Source code must be made available when distributed
- Network use is considered distribution (AGPL requirement)
- Changes must be documented
- Same license must be used for derivative works

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - UI library
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases with Python
- [Vite](https://vitejs.dev/) - Next generation frontend tooling
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Playwright](https://playwright.dev/) - E2E testing
- [Vitest](https://vitest.dev/) - Unit testing

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/data-detective/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/data-detective/discussions)
- **Documentation**: [docs/](docs/)

---

<div align="center">

**Made with ❤️ for educators and students**

[⬆ Back to Top](#-data-detective-academy)

</div>
