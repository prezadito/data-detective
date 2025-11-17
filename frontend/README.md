# Data Detective - Frontend

React + TypeScript + Vite frontend for the Data Detective SQL learning platform.

## Technology Stack

- **React** 19.2.0 - UI library
- **TypeScript** 5.9.3 - Type-safe JavaScript (strict mode enabled)
- **Vite** 7.2.2 - Fast build tool and dev server
- **Tailwind CSS** 4.1.17 - Utility-first CSS framework
- **React Router DOM** 7.9.6 - Client-side routing
- **Ky** 1.14.0 - HTTP client for API requests

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API service layer
│   │   └── api.ts      # Configured ky HTTP client
│   ├── types/          # TypeScript type definitions
│   │   └── index.ts    # API models (User, Challenge, Submission, etc.)
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   └── contexts/       # React contexts
├── .env.example        # Environment variables template
├── vite.config.ts      # Vite with proxy to backend (port 3000 -> 8000)
├── tailwind.config.js  # Tailwind CSS configuration
└── postcss.config.js   # PostCSS with Tailwind & Autoprefixer
```

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm (package manager)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Copy environment variables
cp .env.example .env

# Install dependencies
pnpm install
```

### Development

```bash
# Start dev server (http://localhost:3000)
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview

# Run linter
pnpm lint

# Type check
pnpm exec tsc --noEmit
```

## Testing

### Unit Tests (Vitest)

```bash
# Run unit tests
pnpm test

# Run tests with UI
pnpm test:ui

# Run tests with coverage
pnpm test:coverage
```

### E2E Tests (Playwright)

End-to-end tests cover critical user journeys using Playwright. Tests run across multiple browsers (Chromium, Firefox) with automatic screenshot and video capture on failure.

#### Prerequisites

1. **Backend must be running** on `http://localhost:8000`
2. **Test users must exist** in the database:
   - Student: `e2e-student@test.com` / `Test123!`
   - Teacher: `e2e-teacher@test.com` / `Test123!`

You can create these users by:
```bash
# Option 1: Register via the UI
# 1. Start the backend server
# 2. Navigate to http://localhost:3000/register
# 3. Create both users with the credentials above

# Option 2: Use backend API or database seeding script
```

#### Running E2E Tests

```bash
# Run all E2E tests (headless)
pnpm test:e2e

# Run tests with UI (interactive mode)
pnpm test:e2e:ui

# Run tests in headed mode (see browser)
pnpm test:e2e:headed

# Run tests in debug mode
pnpm test:e2e:debug

# View test report
pnpm test:e2e:report
```

#### Test Structure

```
tests/e2e/
├── fixtures/
│   └── auth.ts           # Authentication fixtures & test users
├── support/
│   └── helpers.ts        # Common test utilities
├── student.spec.ts       # Student user journey tests
└── teacher.spec.ts       # Teacher user journey tests
```

#### Test Coverage

**Student Tests** (`student.spec.ts`):
- Authentication (register, login, logout)
- Challenge solving workflow
- Progress tracking
- Leaderboard interaction
- Navigation and routing

**Teacher Tests** (`teacher.spec.ts`):
- Teacher authentication
- Student management (list, search, sort)
- Student detail view
- Analytics dashboard
- Data visualization (charts)

#### Test Artifacts

Test results are saved to:
- **Screenshots**: `test-results/screenshots/` (on failure)
- **Videos**: `test-results/` (on failure)
- **Traces**: `test-results/` (on failure)
- **HTML Report**: `playwright-report/`

#### Playwright Configuration

The `playwright.config.ts` includes:
- Multi-browser testing (Chromium, Firefox)
- Parallel test execution (4 workers)
- Automatic screenshot/video on failure
- Auto-start dev server
- Retry logic for flaky tests (CI only)

#### Troubleshooting E2E Tests

**Tests fail immediately:**
- Ensure backend is running on port 8000
- Verify test users exist in database
- Check that frontend dev server can start on port 3000

**Authentication tests fail:**
- Verify test user credentials are correct
- Check that backend authentication endpoints are working
- Clear browser storage: `localStorage.clear()`

**Timeout errors:**
- Increase timeout in `playwright.config.ts`
- Check network connectivity to backend
- Verify API responses are not delayed

**Flaky tests:**
- Tests use `waitFor` helpers to handle async operations
- Auto-refresh is disabled in tests to prevent race conditions
- Increase `expect.timeout` if assertions are timing out

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Application Configuration
VITE_APP_NAME=Data Detective
VITE_APP_VERSION=1.0.0

# Environment
VITE_ENV=development
```

### Vite Configuration

The Vite config includes:
- **Path alias**: `@/*` → `./src/*`
- **Dev server**: Port 3000
- **API proxy**: `/api` → `http://localhost:8000`
- **HMR**: Hot module replacement enabled

### TypeScript Configuration

TypeScript is configured with:
- **Strict mode**: Enabled
- **Target**: ES2022
- **Path aliases**: `@/*` support
- **Module**: ESNext with bundler resolution

## API Service Usage

The `src/services/api.ts` provides a configured ky instance with:
- Automatic JSON parsing
- 30-second timeout
- Retry on network errors (3 attempts)
- JWT token handling
- 401 error handling

### Example Usage

```typescript
import { api } from '@/services/api';

// GET request
const challenges = await api.get('challenges').json();

// POST request
const result = await api.post('submissions', {
  json: {
    challenge_id: 1,
    query: 'SELECT * FROM users'
  }
}).json();

// PUT request
await api.put(`users/${userId}`, {
  json: { full_name: 'John Doe' }
});

// DELETE request
await api.delete(`challenges/${challengeId}`);
```

## Type Definitions

Complete TypeScript types are available in `src/types/index.ts`:

### User Types
- `User` - User object
- `UserRole` - Enum: `teacher` | `student`

### Authentication Types
- `LoginCredentials` - Login request
- `RegisterData` - Registration request
- `AuthResponse` - Auth response with token

### Challenge Types
- `Challenge` - Challenge object
- `ChallengeDifficulty` - Enum: `easy` | `medium` | `hard`

### Submission Types
- `Submission` - Submission object
- `SubmitQueryRequest` - Submit query request
- `SubmitQueryResponse` - Submit query response

### Progress Types
- `StudentProgress` - Student progress statistics

### Utility Types
- `PaginatedResponse<T>` - Generic paginated response
- `ApiError` - API error response

## Tailwind CSS

Tailwind is configured with:
- Content paths: `./index.html`, `./src/**/*.{js,ts,jsx,tsx}`
- PostCSS with Autoprefixer
- Custom directives in `src/index.css`

### Using Tailwind

```tsx
// Example component
function Button({ children }: { children: React.ReactNode }) {
  return (
    <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
      {children}
    </button>
  );
}
```

## Code Style

- Use functional components with hooks
- Prefer named exports for components
- Use TypeScript interfaces for props
- Follow the project's folder structure
- Use path aliases (`@/`) for imports

### Example Component

```tsx
// src/components/ChallengeCard.tsx
import { Challenge } from '@/types';

interface ChallengeCardProps {
  challenge: Challenge;
  onClick?: () => void;
}

export function ChallengeCard({ challenge, onClick }: ChallengeCardProps) {
  return (
    <div className="p-4 border rounded" onClick={onClick}>
      <h3 className="text-lg font-bold">{challenge.title}</h3>
      <p className="text-gray-600">{challenge.description}</p>
      <span className="text-sm">{challenge.difficulty}</span>
    </div>
  );
}
```

## Backend Integration

The frontend is configured to proxy API requests to the backend:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API calls to `/api/*` are automatically proxied

Make sure the backend is running before starting the frontend dev server.

## Building for Production

```bash
# Build the project
pnpm build

# Output will be in the 'dist' directory
# Serve with any static file server
```

The production build is optimized with:
- Code splitting
- Tree shaking
- Minification
- Asset optimization

## License

See the root LICENSE file for details.
