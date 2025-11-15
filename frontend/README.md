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
