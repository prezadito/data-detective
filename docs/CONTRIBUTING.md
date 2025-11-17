# Contributing Guide

Thank you for your interest in contributing to Data Detective Academy! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Report unacceptable behavior to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## Getting Started

### Prerequisites

**Backend Development:**
- Python 3.13+
- uv package manager (`pip install uv`)
- SQLite (for development)
- Familiarity with FastAPI and SQLModel

**Frontend Development:**
- Node.js 18+
- pnpm (`npm install -g pnpm`)
- Familiarity with React, TypeScript, and Tailwind CSS

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/data-detective.git
   cd data-detective
   ```
3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/data-detective.git
   ```

### Development Setup

#### Backend Setup
```bash
cd backend

# Install dependencies
uv sync --all-extras

# Create environment file
cp .env.example .env
# Edit .env and set SECRET_KEY (openssl rand -hex 32)

# Run tests to verify setup
uv run pytest tests/ -v

# Start development server
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
pnpm install

# Create environment file
cp .env.example .env

# Run tests to verify setup
pnpm test

# Start development server
pnpm dev
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# OR for bug fixes
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes
- `test/` - Test additions or modifications
- `chore/` - Build/tooling changes

### 2. Make Your Changes

Follow our [Coding Standards](#coding-standards) and write tests for new functionality.

### 3. Test Your Changes

**Backend:**
```bash
cd backend

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check (implicit with ruff)
```

**Frontend:**
```bash
cd frontend

# Run unit tests
pnpm test

# Run E2E tests (requires backend running)
pnpm test:e2e

# Type check
pnpm exec tsc --noEmit

# Lint
pnpm lint

# Build (ensure no errors)
pnpm build
```

### 4. Commit Your Changes

Follow our [Commit Message Guidelines](#commit-message-guidelines).

```bash
git add .
git commit -m "feat: add user profile editing feature"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub following our [Pull Request Process](#pull-request-process).

---

## Coding Standards

### Backend (Python)

#### Style Guide

We follow **PEP 8** with some modifications enforced by Ruff:
- Line length: **88 characters** (Black style)
- Use **type hints** on all functions
- Use **docstrings** for classes, modules, and public functions
- Prefer **f-strings** over `.format()` or `%` formatting

#### Code Organization

```python
# Standard library imports
import os
from datetime import datetime
from typing import Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

# Local imports
from app.database import get_session
from app.models import User
from app.schemas import UserResponse
```

#### Type Hints

```python
# Always use type hints
def get_user(user_id: int, session: Session) -> User | None:
    """Get a user by ID."""
    return session.get(User, user_id)

# Use Optional for nullable values (or | None in Python 3.10+)
def find_user(email: str, session: Session) -> User | None:
    """Find a user by email."""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()
```

#### Docstrings

```python
def submit_challenge(
    unit_id: int,
    challenge_id: int,
    query: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> SubmitQueryResponse:
    """
    Submit a challenge solution.

    Args:
        unit_id: The unit ID
        challenge_id: The challenge ID
        query: The SQL query submitted
        session: Database session (injected)
        current_user: Current authenticated user (injected)

    Returns:
        SubmitQueryResponse with correctness and points

    Raises:
        HTTPException: If challenge not found or already completed
    """
    # Implementation
```

#### Error Handling

```python
# Use HTTPException for API errors
from fastapi import HTTPException

if not challenge:
    raise HTTPException(
        status_code=404,
        detail="Challenge not found"
    )

# Use specific status codes
# 400 - Bad Request (client error)
# 401 - Unauthorized (authentication required)
# 403 - Forbidden (insufficient permissions)
# 404 - Not Found
# 422 - Unprocessable Entity (validation error)
```

#### Database Patterns

```python
# Always use select() for queries
from sqlmodel import select

# Good
statement = select(User).where(User.email == email)
user = session.exec(statement).first()

# Bad - don't use raw SQL
# user = session.execute("SELECT * FROM users WHERE email = ?", email)

# Always refresh after commit to get DB-assigned values
user = User(email=email, name=name)
session.add(user)
session.commit()
session.refresh(user)  # Get the ID assigned by database
```

### Frontend (TypeScript/React)

#### Style Guide

- Use **TypeScript strict mode**
- Use **functional components** with hooks
- Use **named exports** (not default exports)
- Prefer **interfaces** over types for object shapes
- Use **path aliases** (`@/`) for imports

#### Component Structure

```tsx
// 1. Imports
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import type { User } from '@/types';

// 2. Type definitions
interface UserProfileProps {
  userId: number;
  onUpdate?: (user: User) => void;
}

// 3. Component (named export)
export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  // 3a. State and hooks
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // 3b. Effects
  useEffect(() => {
    fetchUser();
  }, [userId]);

  // 3c. Event handlers
  const handleUpdate = async () => {
    // Implementation
  };

  // 3d. Render
  return (
    <div className="p-4">
      {loading ? <Loading /> : <UserInfo user={user} />}
      <Button onClick={handleUpdate}>Update</Button>
    </div>
  );
}
```

#### TypeScript Best Practices

```typescript
// Use interfaces for props
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

// Use types for unions and utilities
type Status = 'idle' | 'loading' | 'success' | 'error';
type UserRole = 'student' | 'teacher';

// Avoid 'any' - use 'unknown' or specific types
// Bad
const handleData = (data: any) => { };

// Good
const handleData = (data: unknown) => {
  if (typeof data === 'object' && data !== null) {
    // Type narrowing
  }
};

// Use type guards
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value
  );
}
```

#### React Best Practices

```tsx
// Use descriptive variable names
// Bad
const [d, setD] = useState(null);

// Good
const [data, setData] = useState<User[]>([]);

// Memoize expensive computations
const sortedUsers = useMemo(() => {
  return users.sort((a, b) => b.points - a.points);
}, [users]);

// Use callbacks to prevent re-renders
const handleSubmit = useCallback(() => {
  // Implementation
}, [dependencies]);

// Destructure props
// Bad
function Component(props: ComponentProps) {
  return <div>{props.title}</div>;
}

// Good
function Component({ title, description }: ComponentProps) {
  return <div>{title}</div>;
}
```

#### Accessibility

```tsx
// Always include ARIA labels for interactive elements
<button
  aria-label="Close modal"
  onClick={onClose}
>
  <X />
</button>

// Use semantic HTML
<nav>
  <ul>
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

// Support keyboard navigation
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  Click me
</div>

// Provide alt text for images
<img src={avatar} alt={`${user.name}'s avatar`} />
```

---

## Testing Requirements

### Backend Testing

**All new features must include tests.**

#### Unit Tests

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.models import User

def test_register_user(client: TestClient):
    """Test user registration."""
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "name": "New User",
        "password": "SecurePass123!",
        "role": "student"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newuser@example.com"
    assert "access_token" in data

def test_login_invalid_credentials(client: TestClient):
    """Test login with invalid credentials."""
    response = client.post("/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
```

#### Test Coverage

- Aim for **>80% code coverage**
- Focus on critical paths (auth, challenge submission)
- Test error cases, not just happy paths

```bash
# Run with coverage report
uv run pytest tests/ --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Frontend Testing

#### Unit Tests (Vitest)

```typescript
// src/components/ui/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../Button';
import { describe, it, expect, vi } from 'vitest';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Submit</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

#### E2E Tests (Playwright)

Add E2E tests for new user flows:

```typescript
// tests/e2e/challenge-submission.spec.ts
import { test, expect } from '@playwright/test';

test('student can submit challenge', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'student@test.com');
  await page.fill('[name="password"]', 'Test123!');
  await page.click('button[type="submit"]');

  // Navigate to challenge
  await page.click('text=Challenges');
  await page.click('text=SELECT All Columns');

  // Submit query
  await page.fill('textarea', 'SELECT * FROM users');
  await page.click('text=Submit');

  // Verify success
  await expect(page.locator('text=Correct!')).toBeVisible();
});
```

---

## Pull Request Process

### Before Submitting

- [ ] All tests pass (`pytest` for backend, `pnpm test` for frontend)
- [ ] No linting errors (`ruff check .` for backend, `pnpm lint` for frontend)
- [ ] Code is formatted (`ruff format .` for backend)
- [ ] Type checking passes (`pnpm exec tsc --noEmit` for frontend)
- [ ] New features have tests
- [ ] Documentation is updated (if applicable)
- [ ] Commit messages follow guidelines

### PR Title

Use conventional commit format:

```
feat(auth): add password reset functionality
fix(leaderboard): correct point calculation
docs(api): update authentication endpoints
refactor(frontend): simplify query editor component
test(backend): add progress tracking tests
```

### PR Description Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Related Issues
Closes #123

## Changes Made
- Added password reset API endpoint
- Created password reset email template
- Added frontend password reset form
- Updated documentation

## Testing
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] E2E tests pass (if applicable)
- [ ] Manual testing completed

## Screenshots (if applicable)
![Screenshot](url)

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing unit tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: Maintainers review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, a maintainer will merge

**Be responsive to feedback and questions.**

---

## Issue Guidelines

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for solutions
3. **Verify it's reproducible** in the latest version

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Backend version: [e.g., 1.0.0]
- Frontend version: [e.g., 1.0.0]

**Additional context**
Any other information about the problem.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots.

**Implementation ideas**
Optional: How you think it could be implemented.
```

---

## Commit Message Guidelines

We follow **Conventional Commits** specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process or tooling changes
- `ci`: CI/CD changes

### Scope (Optional)

- `auth`: Authentication
- `challenges`: Challenges system
- `leaderboard`: Leaderboard
- `analytics`: Analytics
- `ui`: UI components
- `api`: API endpoints

### Examples

```bash
# Simple commit
git commit -m "feat(auth): add password reset"

# With body
git commit -m "fix(leaderboard): correct point calculation

Points were not being calculated correctly when hints were used.
This fixes the calculation to properly subtract hint penalties."

# Breaking change
git commit -m "feat(api)!: change authentication token format

BREAKING CHANGE: Access tokens now use JWT RS256 instead of HS256.
Clients must update their token validation logic."
```

---

## Documentation

### When to Update Documentation

- **New features**: Update relevant docs
- **API changes**: Update API.md
- **Configuration changes**: Update .env.example and docs
- **Architecture changes**: Update ARCHITECTURE.md
- **New components**: Update COMPONENTS.md

### Documentation Standards

- Use **clear, concise language**
- Include **code examples**
- Keep **examples up-to-date**
- Use **proper Markdown formatting**
- Add **table of contents** for long documents

### Documentation Files

- `README.md` - Project overview and quick start
- `docs/ARCHITECTURE.md` - System architecture
- `docs/API.md` - API reference
- `docs/COMPONENTS.md` - Component library
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/CONTRIBUTING.md` - This file
- `docs/TROUBLESHOOTING.md` - Common issues
- `CLAUDE.md` - AI assistant guide

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code contributions

### Getting Help

If you're stuck:
1. Check the documentation
2. Search existing issues
3. Ask in GitHub Discussions
4. Create a new issue if needed

### Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes
- Project README (for significant contributions)

---

## First-Time Contributors

### Good First Issues

Look for issues labeled `good-first-issue` - these are:
- Well-defined and scoped
- Don't require deep knowledge of the codebase
- Have clear acceptance criteria

### Mentorship

First-time contributors can:
- Ask questions in GitHub Discussions
- Request guidance on issues
- Pair program with maintainers (if available)

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (AGPL-3.0).

---

## Questions?

If you have questions about contributing:
- Open a GitHub Discussion
- Comment on the relevant issue
- Reach out to maintainers

**Thank you for contributing to Data Detective Academy!** 🎉

---

*Last updated: 2025-11-17*
