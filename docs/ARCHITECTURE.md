# Architecture Guide

This document provides a comprehensive overview of the Data Detective Academy architecture, including system design, data flow, component interactions, and technical decisions.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Database Schema](#database-schema)
- [Authentication Flow](#authentication-flow)
- [Data Flow](#data-flow)
- [Caching Strategy](#caching-strategy)
- [Technology Decisions](#technology-decisions)
- [Security Considerations](#security-considerations)

---

## System Overview

Data Detective Academy is a **full-stack monorepo** application with separate backend and frontend codebases that communicate via RESTful HTTP APIs.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         React Frontend (TypeScript)                  │   │
│  │  - Vite Dev Server (Port 3000)                       │   │
│  │  - React Router (Client-side routing)                │   │
│  │  - Ky HTTP Client (API communication)                │   │
│  │  - AuthContext (Global auth state)                   │   │
│  └──────────────────┬───────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      │ HTTP/JSON (REST API)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              FastAPI Backend (Python)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  FastAPI Application (Port 8000)                      │  │
│  │  - 13 API Routers (auth, users, challenges, etc.)    │  │
│  │  - JWT Authentication Middleware                      │  │
│  │  - Dependency Injection (database sessions)           │  │
│  │  - Response Caching (leaderboard, analytics)          │  │
│  └──────────────────┬────────────────────────────────────┘  │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      │ SQLModel ORM
                      │
┌─────────────────────▼────────────────────────────────────────┐
│                    Database Layer                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  SQLite (Development) / PostgreSQL (Production)        │ │
│  │  - 6 Tables: User, RefreshToken, PasswordResetToken,  │ │
│  │    Progress, Hint, Attempt                             │ │
│  │  - Indexes on email, tokens                            │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagram

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Pages      │  │  Components  │  │  Contexts    │            │
│  │              │  │              │  │              │            │
│  │ - Login      │  │ - Auth       │  │ - AuthContext│            │
│  │ - Register   │  │ - Challenge  │  └──────┬───────┘            │
│  │ - Dashboard  │  │ - Query      │         │                    │
│  │ - Challenges │  │ - Leaderboard│         │                    │
│  │ - Teacher    │  │ - Progress   │         │                    │
│  └──────┬───────┘  └──────┬───────┘         │                    │
│         │                 │                 │                    │
│         └────────┬────────┘                 │                    │
│                  │                          │                    │
│         ┌────────▼────────┐        ┌────────▼────────┐           │
│         │   React Router  │        │  Service Layer  │           │
│         │   (Navigation)  │        │                 │           │
│         └─────────────────┘        │ - api.ts        │           │
│                                    │ - auth.ts       │           │
│                                    │ - challenges.ts │           │
│                                    └────────┬────────┘           │
│                                             │                    │
└─────────────────────────────────────────────┼────────────────────┘
                                              │
                                              │ HTTP/REST API
                                              │ (JSON)
┌─────────────────────────────────────────────▼────────────────────┐
│                         BACKEND LAYER                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                    │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │              13 API Routers                        │  │   │
│  │  │                                                    │  │   │
│  │  │  /auth         - Authentication & Registration    │  │   │
│  │  │  /users        - User management                   │  │   │
│  │  │  /challenges   - Challenge browsing                │  │   │
│  │  │  /progress     - Progress tracking & submission    │  │   │
│  │  │  /leaderboard  - Leaderboard (cached)              │  │   │
│  │  │  /analytics    - Class analytics (cached)          │  │   │
│  │  │  /export       - CSV data export                   │  │   │
│  │  │  /bulk_import  - CSV student import                │  │   │
│  │  │  /hints        - Hint access tracking              │  │   │
│  │  │  /reports      - Weekly progress reports (cached)  │  │   │
│  │  │  /custom_challenges - Custom challenge management  │  │   │
│  │  │  /datasets     - Dataset management                │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │           Middleware & Dependencies                │  │   │
│  │  │                                                    │  │   │
│  │  │  - OAuth2PasswordBearer (JWT extraction)          │  │   │
│  │  │  - get_session() (Database session injection)     │  │   │
│  │  │  - get_current_user() (Authentication)            │  │   │
│  │  │  - require_student() (Role check)                 │  │   │
│  │  │  - require_teacher() (Role check)                 │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  └────────────────────────┬───────────────────────────────────┘   │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐  │
│  │              Core Application Modules                      │  │
│  │                                                             │  │
│  │  - models.py     (SQLModel database models)                │  │
│  │  - schemas.py    (Pydantic request/response schemas)       │  │
│  │  - auth.py       (JWT & password utilities)                │  │
│  │  - database.py   (Database connection & session)           │  │
│  │  - challenges.py (Hardcoded challenge definitions)         │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                       │
└───────────────────────────┼───────────────────────────────────────┘
                            │
                            │ SQLModel ORM
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                      DATABASE LAYER                               │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │    User     │  │ RefreshToken │  │ PasswordResetToken     │  │
│  │             │  │              │  │                        │  │
│  │ - id        │  │ - id         │  │ - id                   │  │
│  │ - email     │  │ - token      │  │ - token                │  │
│  │ - name      │  │ - user_id FK │  │ - user_id FK           │  │
│  │ - role      │  │ - expires_at │  │ - expires_at           │  │
│  │ - password  │  │ - revoked    │  │ - used                 │  │
│  └─────┬───────┘  └──────────────┘  └────────────────────────┘  │
│        │                                                          │
│        │ One-to-Many                                              │
│        │                                                          │
│  ┌─────▼────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  Progress    │  │    Hint      │  │      Attempt           │ │
│  │              │  │              │  │                        │ │
│  │ - id         │  │ - id         │  │ - id                   │ │
│  │ - user_id FK │  │ - user_id FK │  │ - user_id FK           │ │
│  │ - unit_id    │  │ - unit_id    │  │ - unit_id              │ │
│  │ - challenge  │  │ - challenge  │  │ - challenge_id         │ │
│  │ - points     │  │ - hint_level │  │ - query                │ │
│  │ - hints_used │  │ - accessed   │  │ - is_correct           │ │
│  │ - query      │  │              │  │ - attempted_at         │ │
│  │ - completed  │  └──────────────┘  └────────────────────────┘ │
│  └──────────────┘                                                │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Design Patterns

#### 1. **Modular Router Organization**

The backend uses FastAPI's router system to organize endpoints by domain:

```python
# backend/app/main.py
from fastapi import FastAPI
from app.routes import auth, users, challenges, progress, leaderboard

app = FastAPI(title="Data Detective Academy API")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(challenges.router, prefix="/challenges", tags=["Challenges"])
# ... 10 more routers
```

#### 2. **Dependency Injection Pattern**

FastAPI's dependency injection is used extensively for:

- **Database Session Management**:
  ```python
  def get_session() -> Generator[Session, None, None]:
      with Session(engine) as session:
          yield session

  @router.get("/users")
  def get_users(session: Session = Depends(get_session)):
      # session automatically provided and cleaned up
  ```

- **Authentication**:
  ```python
  async def get_current_user(
      token: str = Depends(oauth2_scheme),
      session: Session = Depends(get_session)
  ) -> User:
      # Decode JWT, validate, return user

  @router.get("/profile")
  def get_profile(current_user: User = Depends(get_current_user)):
      return current_user
  ```

- **Role-Based Access Control**:
  ```python
  def require_teacher(current_user: User = Depends(get_current_user)) -> User:
      if current_user.role != "teacher":
          raise HTTPException(status_code=403)
      return current_user
  ```

#### 3. **Separation of Models and Schemas**

**Critical Pattern**: Database models are never exposed directly in API responses.

- **Models** (`app/models.py`): Database tables with SQLModel
  - Include sensitive fields (password_hash, tokens)
  - Used only for database operations

- **Schemas** (`app/schemas.py`): Pydantic models for API
  - Exclude sensitive fields
  - Used for request/response validation
  - 58 different schemas for different use cases

```python
# Model (database)
class User(SQLModel, table=True):
    id: int | None = None
    email: str
    password_hash: str  # NEVER expose this!
    name: str
    role: str

# Schema (API response)
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    # password_hash is excluded
```

#### 4. **Lifespan Management**

Modern FastAPI async context manager for startup/shutdown:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(lifespan=lifespan)
```

### Backend Layer Structure

```
app/
├── routes/              # API endpoints (13 routers)
│   ├── __init__.py
│   ├── auth.py          # POST /auth/register, /auth/login, etc.
│   ├── users.py         # GET /users, GET /users/{id}, etc.
│   ├── challenges.py    # GET /challenges
│   ├── progress.py      # POST /progress/submit, GET /progress/me
│   ├── leaderboard.py   # GET /leaderboard (cached)
│   ├── analytics.py     # GET /analytics/class (teacher, cached)
│   ├── export.py        # GET /export/students, /export/progress
│   ├── bulk_import.py   # POST /import/students
│   ├── hints.py         # GET /hints, POST /hints/access
│   ├── reports.py       # GET /reports/weekly (cached)
│   ├── custom_challenges.py  # Custom challenge CRUD
│   └── datasets.py      # Dataset management
│
├── models.py            # 6 SQLModel tables
├── schemas.py           # 58 Pydantic schemas
├── auth.py              # JWT & bcrypt utilities
├── database.py          # Engine, session, initialization
├── challenges.py        # Hardcoded challenge definitions
└── main.py              # FastAPI app, router registration
```

---

## Frontend Architecture

### Design Patterns

#### 1. **Component-Based Architecture**

React components are organized by domain:

```
components/
├── auth/            # LoginForm, RegisterForm
├── challenge/       # ChallengeCard, SchemaView, HintSystem
├── leaderboard/     # LeaderboardTable
├── navigation/      # Navigation (navbar)
├── progress/        # Progress tracking components
├── query/           # SQL query editor
├── routing/         # ProtectedRoute, RoleProtectedRoute
├── teacher/         # Teacher dashboard components
└── ui/              # Reusable primitives (Button, Input, Modal)
```

#### 2. **Service Layer Pattern**

API calls are abstracted into service modules to separate business logic from UI:

```typescript
// services/api.ts - Configured HTTP client
import ky from 'ky';

export const api = ky.create({
  prefixUrl: import.meta.env.VITE_API_URL,
  timeout: 30000,
  retry: 3,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      }
    ],
    afterResponse: [
      async (request, options, response) => {
        if (response.status === 401) {
          // Handle token refresh or logout
        }
      }
    ]
  }
});

// services/challenges.ts - Challenge-specific API
export const getChallenges = () =>
  api.get('challenges').json<Challenge[]>();

export const submitQuery = (data: SubmitQueryRequest) =>
  api.post('progress/submit', { json: data }).json<SubmitQueryResponse>();
```

#### 3. **Context API for Global State**

`AuthContext` manages authentication state globally:

```typescript
// contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  // Load user from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Validate and load user
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### 4. **Protected Route Pattern**

Route guards based on authentication and role:

```typescript
// components/routing/ProtectedRoute.tsx
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
}

// components/routing/RoleProtectedRoute.tsx
export function RoleProtectedRoute({
  children,
  allowedRoles
}: {
  children: ReactNode;
  allowedRoles: UserRole[]
}) {
  const { user } = useAuth();

  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" />;
  }

  return <>{children}</>;
}
```

### Frontend Layer Structure

```
src/
├── components/      # Reusable React components
├── pages/           # Route-level page components
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── DashboardPage.tsx
│   ├── ChallengesPage.tsx
│   ├── LeaderboardPage.tsx
│   └── teacher/
│       ├── TeacherDashboard.tsx
│       ├── StudentListPage.tsx
│       └── AnalyticsPage.tsx
├── contexts/        # React contexts
│   └── AuthContext.tsx
├── services/        # API service layer
│   ├── api.ts       # Configured ky client
│   ├── auth.ts      # Auth API calls
│   └── challenges.ts
├── hooks/           # Custom React hooks
├── types/           # TypeScript type definitions
├── utils/           # Utility functions
└── App.tsx          # Root component with routing
```

---

## Database Schema

### Entity-Relationship Overview

```
┌─────────────────┐
│      User       │
│─────────────────│
│ • id (PK)       │
│ • email (UNIQUE)│
│ • name          │
│ • role          │──┐
│ • password_hash │  │
│ • created_at    │  │
│ • last_login    │  │
└─────────────────┘  │
                     │ 1:N
        ┌────────────┼────────────┬────────────┐
        │            │            │            │
┌───────▼───────┐ ┌──▼─────────┐ ┌▼──────────┐ ┌▼──────────────────┐
│  Progress     │ │   Hint     │ │  Attempt  │ │  RefreshToken     │
│───────────────│ │────────────│ │───────────│ │───────────────────│
│ • id (PK)     │ │ • id (PK)  │ │ • id (PK) │ │ • id (PK)         │
│ • user_id (FK)│ │ • user_id  │ │ • user_id │ │ • user_id (FK)    │
│ • unit_id     │ │ • unit_id  │ │ • unit_id │ │ • token (UNIQUE)  │
│ • challenge_id│ │ • challenge│ │ • query   │ │ • expires_at      │
│ • points_earn │ │ • hint_lvl │ │ • correct │ │ • revoked         │
│ • hints_used  │ │ • accessed │ │ • attempt │ └───────────────────┘
│ • query       │ └────────────┘ └───────────┘
│ • completed   │
└───────────────┘
     UNIQUE(user_id, unit_id, challenge_id)
```

### Table Details

#### **User Table**
- **Purpose**: Store student and teacher accounts
- **Indexes**: Unique index on `email`
- **Roles**: `student`, `teacher`
- **Password Security**: Bcrypt hashed (starts with `$2b$`)

#### **RefreshToken Table**
- **Purpose**: Long-lived JWT refresh tokens (7 days)
- **Indexes**: Unique index on `token`
- **Revocation**: `revoked` boolean for logout

#### **PasswordResetToken Table**
- **Purpose**: Time-limited password reset tokens
- **Indexes**: Unique index on `token`
- **Expiration**: 1 hour TTL
- **One-time Use**: `used` boolean

#### **Progress Table**
- **Purpose**: Track completed challenges
- **Constraint**: Unique per (user_id, unit_id, challenge_id)
- **Points**: Base challenge points minus hint penalties

#### **Hint Table**
- **Purpose**: Track every hint access
- **No Unique Constraint**: Allows multiple accesses
- **Point Penalty**: Each hint access tracked separately

#### **Attempt Table**
- **Purpose**: Track all challenge attempts (correct & incorrect)
- **No Unique Constraint**: Unlimited attempts allowed
- **Analytics**: Used for teacher analytics

---

## Authentication Flow

### Registration Flow

```
┌─────────┐                                                      ┌─────────┐
│ Browser │                                                      │ Backend │
└────┬────┘                                                      └────┬────┘
     │                                                                │
     │  POST /auth/register                                           │
     │  { email, name, password, role }                               │
     │───────────────────────────────────────────────────────────────>│
     │                                                                │
     │                                          1. Validate email     │
     │                                          2. Hash password      │
     │                                          3. Create user in DB  │
     │                                          4. Generate JWT       │
     │                                                                │
     │  200 OK                                                        │
     │  { access_token, refresh_token, user: {...} }                 │
     │<───────────────────────────────────────────────────────────────│
     │                                                                │
     │  Store tokens in localStorage                                 │
     │  Update AuthContext                                            │
     │                                                                │
```

### Login Flow

```
┌─────────┐                                                      ┌─────────┐
│ Browser │                                                      │ Backend │
└────┬────┘                                                      └────┬────┘
     │                                                                │
     │  POST /auth/login                                              │
     │  { email, password }                                           │
     │───────────────────────────────────────────────────────────────>│
     │                                                                │
     │                                          1. Find user by email │
     │                                          2. Verify password    │
     │                                          3. Generate JWT       │
     │                                          4. Save refresh token │
     │                                                                │
     │  200 OK                                                        │
     │  { access_token, refresh_token, user: {...} }                 │
     │<───────────────────────────────────────────────────────────────│
     │                                                                │
     │  Store tokens in localStorage                                 │
     │  Redirect to dashboard                                         │
     │                                                                │
```

### Authenticated Request Flow

```
┌─────────┐                                                      ┌─────────┐
│ Browser │                                                      │ Backend │
└────┬────┘                                                      └────┬────┘
     │                                                                │
     │  GET /challenges                                               │
     │  Authorization: Bearer {access_token}                          │
     │───────────────────────────────────────────────────────────────>│
     │                                                                │
     │                                          1. Extract JWT token  │
     │                                          2. Verify signature   │
     │                                          3. Check expiration   │
     │                                          4. Get user from DB   │
     │                                          5. Execute request    │
     │                                                                │
     │  200 OK                                                        │
     │  { challenges: [...] }                                         │
     │<───────────────────────────────────────────────────────────────│
     │                                                                │
```

### Token Refresh Flow

```
┌─────────┐                                                      ┌─────────┐
│ Browser │                                                      │ Backend │
└────┬────┘                                                      └────┬────┘
     │                                                                │
     │  GET /challenges                                               │
     │  Authorization: Bearer {expired_access_token}                  │
     │───────────────────────────────────────────────────────────────>│
     │                                                                │
     │  401 Unauthorized                                              │
     │  { detail: "Token expired" }                                   │
     │<───────────────────────────────────────────────────────────────│
     │                                                                │
     │  POST /auth/refresh                                            │
     │  { refresh_token }                                             │
     │───────────────────────────────────────────────────────────────>│
     │                                                                │
     │                                          1. Validate refresh   │
     │                                          2. Check not revoked  │
     │                                          3. Generate new access│
     │                                                                │
     │  200 OK                                                        │
     │  { access_token, refresh_token }                               │
     │<───────────────────────────────────────────────────────────────│
     │                                                                │
     │  Update localStorage                                           │
     │  Retry original request                                        │
     │                                                                │
```

---

## Data Flow

### Challenge Submission Flow

```
┌──────────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│ Student  │          │ Frontend │          │ Backend  │          │ Database │
│ Browser  │          │ Service  │          │   API    │          │          │
└────┬─────┘          └────┬─────┘          └────┬─────┘          └────┬─────┘
     │                     │                     │                     │
     │ 1. Type SQL query   │                     │                     │
     │ in editor           │                     │                     │
     │────────────────────>│                     │                     │
     │                     │                     │                     │
     │ 2. Click Submit     │                     │                     │
     │────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ 3. POST /progress/  │                     │
     │                     │    submit           │                     │
     │                     │ { unit_id,          │                     │
     │                     │   challenge_id,     │                     │
     │                     │   query }           │                     │
     │                     │────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ 4. Record attempt   │
     │                     │                     │────────────────────>│
     │                     │                     │                     │
     │                     │                     │ 5. Validate query   │
     │                     │                     │ (normalize & match) │
     │                     │                     │                     │
     │                     │                     │ 6. Calculate points │
     │                     │                     │ (base - hint penalty)│
     │                     │                     │                     │
     │                     │                     │ 7. Save progress    │
     │                     │                     │────────────────────>│
     │                     │                     │                     │
     │                     │                     │ 8. Invalidate cache │
     │                     │                     │ (leaderboard,       │
     │                     │                     │  analytics, reports)│
     │                     │                     │                     │
     │                     │ 9. Return result    │                     │
     │                     │ { is_correct,       │                     │
     │                     │   points_earned,    │                     │
     │                     │   feedback }        │                     │
     │                     │<────────────────────│                     │
     │                     │                     │                     │
     │ 10. Display result  │                     │                     │
     │<────────────────────│                     │                     │
     │ (confetti if correct│                     │                     │
     │  or error message)  │                     │                     │
     │                     │                     │                     │
```

### Teacher Analytics Flow

```
┌──────────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│ Teacher  │          │ Frontend │          │ Backend  │          │ Database │
│ Browser  │          │          │          │   API    │          │  Cache   │
└────┬─────┘          └────┬─────┘          └────┬─────┘          └────┬─────┘
     │                     │                     │                     │
     │ 1. Navigate to      │                     │                     │
     │    /teacher/analytics│                     │                     │
     │────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ 2. GET /analytics/  │                     │
     │                     │    class            │                     │
     │                     │────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ 3. Check cache      │
     │                     │                     │────────────────────>│
     │                     │                     │                     │
     │                     │                     │ 4. Cache HIT        │
     │                     │                     │ (1-hour TTL)        │
     │                     │                     │<────────────────────│
     │                     │                     │                     │
     │                     │ 5. Return analytics │                     │
     │                     │ { avg_completion,   │                     │
     │                     │   top_performers,   │                     │
     │                     │   struggling,       │                     │
     │                     │   challenge_stats } │                     │
     │                     │<────────────────────│                     │
     │                     │                     │                     │
     │ 6. Render charts    │                     │                     │
     │    and tables       │                     │                     │
     │<────────────────────│                     │                     │
     │                     │                     │                     │
```

---

## Caching Strategy

### In-Memory Caching

The backend uses Python dictionaries for in-memory caching with TTL:

```python
# backend/app/routes/leaderboard.py
cache = {}
CACHE_TTL = 300  # 5 minutes

@router.get("/leaderboard")
def get_leaderboard(session: Session = Depends(get_session)):
    now = datetime.now()

    # Check cache
    if "leaderboard" in cache:
        data, timestamp = cache["leaderboard"]
        if (now - timestamp).total_seconds() < CACHE_TTL:
            return data

    # Cache MISS - query database
    leaderboard = session.exec(
        select(User, func.sum(Progress.points_earned))
        .join(Progress)
        .group_by(User.id)
        .order_by(func.sum(Progress.points_earned).desc())
        .limit(100)
    ).all()

    # Store in cache
    cache["leaderboard"] = (leaderboard, now)
    return leaderboard
```

### Cached Endpoints

| Endpoint | TTL | Invalidation Trigger |
|----------|-----|---------------------|
| `GET /leaderboard` | 5 minutes | Progress submission, bulk import |
| `GET /analytics/class` | 1 hour | Progress submission, bulk import |
| `GET /reports/weekly` | 1 hour | Progress submission, bulk import |

### Cache Invalidation

```python
def invalidate_all_caches():
    """Called after progress updates or bulk import"""
    cache.clear()  # Simple but effective
```

**Why in-memory caching?**
- Simple implementation
- No external dependencies (Redis, Memcached)
- Sufficient for educational workload
- Easy to debug and reason about

**Limitations:**
- Cache doesn't survive server restart
- Not shared across multiple server instances
- For production at scale, consider Redis

---

## Technology Decisions

### Why FastAPI?

- **Performance**: Async support, one of the fastest Python frameworks
- **Type Safety**: Pydantic validation, automatic OpenAPI docs
- **Modern**: Python 3.13+ features, type hints everywhere
- **Developer Experience**: Auto-generated API docs, excellent error messages

### Why SQLModel?

- **Dual Purpose**: Database ORM + Pydantic validation in one
- **Type Safety**: Full type hints, IDE autocomplete
- **SQLAlchemy Power**: Built on SQLAlchemy, but simpler
- **FastAPI Integration**: Designed by same author (Sebastián Ramírez)

### Why React 19?

- **Latest Features**: React Compiler, improved hooks
- **Performance**: Automatic optimizations
- **TypeScript**: First-class TS support
- **Ecosystem**: Largest component library ecosystem

### Why Vite?

- **Speed**: Lightning-fast HMR (Hot Module Replacement)
- **Modern**: ES modules, optimized builds
- **Simple**: Minimal configuration
- **Developer Experience**: Instant server start

### Why Tailwind CSS?

- **Productivity**: Rapid UI development
- **Consistency**: Design system built-in
- **Performance**: Purges unused CSS
- **Customization**: Easy theme configuration

### Why Ky over Axios?

- **Modern**: Built on Fetch API
- **Smaller**: 4KB vs 14KB (Axios)
- **TypeScript**: Better TS support
- **Browser-first**: Designed for modern browsers

### Why uv package manager?

- **Speed**: 10-100x faster than pip
- **Reliability**: Better dependency resolution
- **Modern**: Written in Rust
- **Compatibility**: Drop-in replacement for pip

### Why pnpm?

- **Disk Efficiency**: Symlinks shared dependencies
- **Speed**: Faster than npm/yarn
- **Strict**: Prevents phantom dependencies
- **Monorepo**: Excellent workspace support

---

## Security Considerations

### Authentication Security

1. **Password Hashing**: Bcrypt with automatic salt
2. **JWT Tokens**: HS256 algorithm, signed with SECRET_KEY
3. **Token Expiration**:
   - Access tokens: 30 minutes (short-lived)
   - Refresh tokens: 7 days (long-lived, revocable)
4. **Refresh Token Revocation**: Stored in database, can be revoked on logout
5. **Password Reset**: Time-limited tokens (1 hour), one-time use

### API Security

1. **CORS**: Configured for frontend origin
2. **Rate Limiting**: Not implemented (TODO for production)
3. **Input Validation**: Pydantic schemas validate all inputs
4. **SQL Injection**: SQLModel prevents SQL injection
5. **XSS Prevention**: React escapes by default
6. **HTTPS**: Required in production

### Data Security

1. **Sensitive Data**: Never expose password_hash in API responses
2. **User Enumeration**: Same error message for invalid email/password
3. **Role-Based Access**: Dependency injection enforces roles
4. **Database**: Use PostgreSQL in production with connection pooling

### Security Headers (TODO for Production)

```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

---

## Future Architectural Considerations

### Scalability

**Current Limitations:**
- In-memory caching doesn't scale horizontally
- SQLite limited to single server
- No WebSocket support for real-time features

**Future Improvements:**
1. **Redis** for distributed caching
2. **PostgreSQL** with connection pooling
3. **WebSockets** for live leaderboard updates
4. **Celery** for background tasks (email, reports)
5. **Docker** for containerization
6. **Kubernetes** for orchestration

### Performance Optimizations

1. **Database Indexing**: Add composite indexes for common queries
2. **Query Optimization**: Use `select_related` for N+1 query prevention
3. **Frontend Code Splitting**: Lazy load routes
4. **CDN**: Serve static assets from CDN
5. **Image Optimization**: Compress and lazy load images

### Monitoring & Observability

1. **Logging**: Structured logging (JSON) with correlation IDs
2. **Metrics**: Prometheus + Grafana
3. **Tracing**: OpenTelemetry for distributed tracing
4. **Error Tracking**: Sentry or similar
5. **Health Checks**: `/health` endpoint for monitoring

---

## Related Documentation

- [API Reference](API.md) - Detailed API endpoint documentation
- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions
- [Contributing Guide](CONTRIBUTING.md) - Development workflow
- [Component Library](COMPONENTS.md) - Frontend component documentation

---

*Last updated: 2025-11-17*
