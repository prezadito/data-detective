# API Reference

Complete REST API documentation for Data Detective Academy.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [Users](#user-endpoints)
  - [Challenges](#challenge-endpoints)
  - [Progress](#progress-endpoints)
  - [Leaderboard](#leaderboard-endpoints)
  - [Hints](#hint-endpoints)
  - [Analytics](#analytics-endpoints)
  - [Export](#export-endpoints)
  - [Bulk Import](#bulk-import-endpoints)
  - [Reports](#report-endpoints)
  - [Custom Challenges](#custom-challenge-endpoints)
  - [Datasets](#dataset-endpoints)
- [Rate Limiting](#rate-limiting)
- [API Clients](#api-clients)

---

## Base URL

**Development:** `http://localhost:8000`
**Production:** `https://your-domain.com`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Authentication

The API uses **JWT (JSON Web Tokens)** for authentication.

### Authentication Flow

1. **Register** or **Login** to receive access and refresh tokens
2. **Include access token** in `Authorization` header for protected endpoints
3. **Refresh token** when access token expires (30 minutes)
4. **Logout** to revoke refresh token

### Token Types

| Token Type | Lifetime | Purpose | Storage |
|------------|----------|---------|---------|
| Access Token | 30 minutes | API authentication | localStorage (frontend) |
| Refresh Token | 7 days | Renew access token | localStorage + Database |

### Adding Token to Requests

```bash
# HTTP Header
Authorization: Bearer {access_token}
```

```typescript
// Frontend (ky example)
const response = await api.get('challenges', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Common Error Examples

**Validation Error (422)**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Authentication Error (401)**
```json
{
  "detail": "Could not validate credentials"
}
```

**Authorization Error (403)**
```json
{
  "detail": "Insufficient permissions"
}
```

---

## Endpoints

### Authentication Endpoints

#### POST /auth/register

Register a new user account.

**Authentication:** None (public)

**Request Body:**
```json
{
  "email": "student@example.com",
  "name": "John Doe",
  "password": "SecurePassword123!",
  "role": "student"
}
```

**Fields:**
- `email` (string, required): Valid email address
- `name` (string, required): Full name
- `password` (string, required): Minimum 8 characters
- `role` (string, required): `"student"` or `"teacher"`

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "student@example.com",
    "name": "John Doe",
    "role": "student",
    "created_at": "2025-11-17T10:00:00",
    "last_login": null
  }
}
```

**Errors:**
- `400`: Email already registered
- `422`: Validation error

**Example (curl):**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "name": "John Doe",
    "password": "SecurePassword123!",
    "role": "student"
  }'
```

---

#### POST /auth/login

Login with existing credentials.

**Authentication:** None (public)

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "student@example.com",
    "name": "John Doe",
    "role": "student",
    "created_at": "2025-11-17T10:00:00",
    "last_login": "2025-11-17T10:30:00"
  }
}
```

**Errors:**
- `401`: Invalid email or password

**Example (curl):**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePassword123!"
  }'
```

---

#### POST /auth/refresh

Refresh an expired access token.

**Authentication:** None (but requires valid refresh token)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401`: Invalid or expired refresh token
- `401`: Refresh token revoked

---

#### POST /auth/logout

Revoke refresh token (logout).

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

#### POST /auth/password-reset-request

Request a password reset token.

**Authentication:** None (public)

**Request Body:**
```json
{
  "email": "student@example.com"
}
```

**Response (200):**
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

**Note:** Always returns 200 to prevent user enumeration.

---

#### POST /auth/password-reset-confirm

Confirm password reset with token.

**Authentication:** None (but requires valid reset token)

**Request Body:**
```json
{
  "token": "abc123def456...",
  "new_password": "NewSecurePassword123!"
}
```

**Response (200):**
```json
{
  "message": "Password successfully reset"
}
```

**Errors:**
- `400`: Invalid or expired token
- `400`: Token already used

---

### User Endpoints

#### GET /users/me

Get current user profile.

**Authentication:** Required

**Response (200):**
```json
{
  "id": 1,
  "email": "student@example.com",
  "name": "John Doe",
  "role": "student",
  "created_at": "2025-11-17T10:00:00",
  "last_login": "2025-11-17T10:30:00"
}
```

**Example (curl):**
```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer {access_token}"
```

---

#### PUT /users/me

Update current user profile.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "John Smith",
  "email": "newemail@example.com"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "name": "John Smith",
  "role": "student",
  "created_at": "2025-11-17T10:00:00",
  "last_login": "2025-11-17T10:30:00"
}
```

---

#### GET /users

List all students (teachers only).

**Authentication:** Required (Teacher role)

**Query Parameters:**
- `offset` (int, default: 0): Pagination offset
- `limit` (int, default: 50): Results per page
- `search` (string, optional): Search by name or email
- `sort_by` (string, optional): `name`, `email`, `created_at`, `points`
- `sort_order` (string, optional): `asc` or `desc`

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "email": "student1@example.com",
      "name": "Student One",
      "role": "student",
      "created_at": "2025-11-17T10:00:00",
      "total_points": 450
    },
    {
      "id": 2,
      "email": "student2@example.com",
      "name": "Student Two",
      "role": "student",
      "created_at": "2025-11-17T11:00:00",
      "total_points": 320
    }
  ],
  "total": 2,
  "offset": 0,
  "limit": 50
}
```

**Example (curl):**
```bash
curl -X GET "http://localhost:8000/users?offset=0&limit=10&search=John&sort_by=points&sort_order=desc" \
  -H "Authorization: Bearer {teacher_access_token}"
```

---

#### GET /users/{user_id}

Get specific student details (teachers only).

**Authentication:** Required (Teacher role)

**Path Parameters:**
- `user_id` (int): Student ID

**Response (200):**
```json
{
  "id": 1,
  "email": "student@example.com",
  "name": "John Doe",
  "role": "student",
  "created_at": "2025-11-17T10:00:00",
  "last_login": "2025-11-17T10:30:00",
  "total_points": 450,
  "challenges_completed": 5,
  "completion_rate": 71.43
}
```

**Errors:**
- `404`: Student not found
- `403`: Not a teacher

---

### Challenge Endpoints

#### GET /challenges

Get all available challenges with statistics.

**Authentication:** Required

**Response (200):**
```json
{
  "challenges": [
    {
      "unit_id": 1,
      "challenge_id": 1,
      "title": "SELECT All Columns",
      "description": "Write a query to select all columns from the users table",
      "difficulty": "easy",
      "points": 100,
      "completed": true,
      "user_points_earned": 100,
      "attempts": 1
    },
    {
      "unit_id": 1,
      "challenge_id": 2,
      "title": "SELECT Specific Columns",
      "description": "Select only name and email from the users table",
      "difficulty": "easy",
      "points": 100,
      "completed": false,
      "user_points_earned": null,
      "attempts": 0
    }
  ]
}
```

**Example (curl):**
```bash
curl -X GET http://localhost:8000/challenges \
  -H "Authorization: Bearer {access_token}"
```

---

### Progress Endpoints

#### POST /progress/submit

Submit a challenge solution.

**Authentication:** Required (Student role)

**Request Body:**
```json
{
  "unit_id": 1,
  "challenge_id": 1,
  "query": "SELECT * FROM users"
}
```

**Response (200) - Correct:**
```json
{
  "is_correct": true,
  "points_earned": 100,
  "total_points": 450,
  "message": "Correct! Well done!",
  "feedback": null
}
```

**Response (200) - Incorrect:**
```json
{
  "is_correct": false,
  "points_earned": 0,
  "total_points": 350,
  "message": "Not quite right. Try again!",
  "feedback": "Your query doesn't match the expected output. Check the column names."
}
```

**Errors:**
- `403`: Not a student
- `404`: Challenge not found
- `400`: Already completed

---

#### GET /progress/me

Get own progress statistics (students).

**Authentication:** Required (Student role)

**Response (200):**
```json
{
  "user_id": 1,
  "total_points": 450,
  "challenges_completed": 5,
  "total_challenges": 7,
  "completion_rate": 71.43,
  "hints_used": 2,
  "total_attempts": 8,
  "completed_challenges": [
    {
      "unit_id": 1,
      "challenge_id": 1,
      "points_earned": 100,
      "hints_used": 0,
      "query": "SELECT * FROM users",
      "completed_at": "2025-11-17T10:00:00"
    }
  ]
}
```

---

#### GET /progress/user/{user_id}

Get student progress (teachers only).

**Authentication:** Required (Teacher role)

**Path Parameters:**
- `user_id` (int): Student ID

**Response (200):**
```json
{
  "user_id": 1,
  "user_name": "John Doe",
  "user_email": "student@example.com",
  "total_points": 450,
  "challenges_completed": 5,
  "total_challenges": 7,
  "completion_rate": 71.43,
  "hints_used": 2,
  "total_attempts": 8,
  "completed_challenges": [
    {
      "unit_id": 1,
      "challenge_id": 1,
      "points_earned": 100,
      "hints_used": 0,
      "completed_at": "2025-11-17T10:00:00"
    }
  ]
}
```

---

### Leaderboard Endpoints

#### GET /leaderboard

Get top 100 students by points (cached 5 minutes).

**Authentication:** Required

**Response (200):**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": 5,
      "name": "Alice Johnson",
      "total_points": 700,
      "challenges_completed": 7
    },
    {
      "rank": 2,
      "user_id": 3,
      "name": "Bob Smith",
      "total_points": 650,
      "challenges_completed": 7
    },
    {
      "rank": 3,
      "user_id": 1,
      "name": "John Doe",
      "total_points": 450,
      "challenges_completed": 5
    }
  ],
  "your_rank": 3,
  "your_points": 450
}
```

**Note:** Results are cached for 5 minutes for performance.

---

### Hint Endpoints

#### GET /hints/{unit_id}/{challenge_id}

Get available hints for a challenge.

**Authentication:** Required (Student role)

**Path Parameters:**
- `unit_id` (int): Unit ID
- `challenge_id` (int): Challenge ID

**Response (200):**
```json
{
  "hints": [
    {
      "level": 1,
      "hint": "Start with the SELECT keyword",
      "point_penalty": 10,
      "accessed": false
    },
    {
      "level": 2,
      "hint": "You need to specify which table to query using FROM",
      "point_penalty": 20,
      "accessed": false
    },
    {
      "level": 3,
      "hint": "The complete query is: SELECT * FROM users",
      "point_penalty": 50,
      "accessed": false
    }
  ]
}
```

---

#### POST /hints/access

Access a hint (applies point penalty).

**Authentication:** Required (Student role)

**Request Body:**
```json
{
  "unit_id": 1,
  "challenge_id": 1,
  "hint_level": 1
}
```

**Response (200):**
```json
{
  "hint": "Start with the SELECT keyword",
  "point_penalty": 10,
  "remaining_points_for_challenge": 90,
  "message": "Hint accessed. This challenge is now worth 90 points."
}
```

---

### Analytics Endpoints

#### GET /analytics/class

Get class-wide analytics (teachers only, cached 1 hour).

**Authentication:** Required (Teacher role)

**Response (200):**
```json
{
  "total_students": 25,
  "active_students": 20,
  "average_completion_rate": 65.5,
  "average_points": 425,
  "total_submissions": 150,
  "challenge_statistics": [
    {
      "unit_id": 1,
      "challenge_id": 1,
      "title": "SELECT All Columns",
      "completion_rate": 85,
      "average_attempts": 1.2,
      "average_hints_used": 0.3
    }
  ],
  "top_performers": [
    {
      "user_id": 5,
      "name": "Alice Johnson",
      "total_points": 700,
      "completion_rate": 100
    }
  ],
  "struggling_students": [
    {
      "user_id": 12,
      "name": "Student Name",
      "total_points": 150,
      "completion_rate": 28.57,
      "last_activity": "2025-11-10T10:00:00"
    }
  ]
}
```

**Note:** Results are cached for 1 hour.

---

### Export Endpoints

#### GET /export/students

Export student list as CSV (teachers only).

**Authentication:** Required (Teacher role)

**Response (200):**
```csv
id,email,name,created_at,total_points,challenges_completed
1,student1@example.com,Student One,2025-11-17T10:00:00,450,5
2,student2@example.com,Student Two,2025-11-17T11:00:00,320,3
```

**Headers:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="students.csv"
```

---

#### GET /export/progress

Export student progress as CSV (teachers only).

**Authentication:** Required (Teacher role)

**Query Parameters:**
- `user_id` (int, optional): Export specific student only

**Response (200):**
```csv
user_id,user_name,unit_id,challenge_id,points_earned,hints_used,completed_at
1,John Doe,1,1,100,0,2025-11-17T10:00:00
1,John Doe,1,2,90,1,2025-11-17T10:15:00
```

---

### Bulk Import Endpoints

#### POST /import/students

Bulk import students from CSV (teachers only).

**Authentication:** Required (Teacher role)

**Request Body (multipart/form-data):**
```
file: students.csv
```

**CSV Format:**
```csv
email,name,password
student1@example.com,Student One,Password123!
student2@example.com,Student Two,Password123!
```

**Response (201):**
```json
{
  "imported": 2,
  "skipped": 0,
  "errors": [],
  "students": [
    {
      "id": 1,
      "email": "student1@example.com",
      "name": "Student One"
    },
    {
      "id": 2,
      "email": "student2@example.com",
      "name": "Student Two"
    }
  ]
}
```

**Response with errors (207):**
```json
{
  "imported": 1,
  "skipped": 1,
  "errors": [
    {
      "row": 2,
      "email": "invalid-email",
      "error": "Invalid email format"
    }
  ],
  "students": [...]
}
```

---

### Report Endpoints

#### GET /reports/weekly

Get weekly progress report (cached 1 hour).

**Authentication:** Required

**Query Parameters:**
- `user_id` (int, optional): Specific user (teachers only)

**Response (200):**
```json
{
  "user_id": 1,
  "user_name": "John Doe",
  "week_start": "2025-11-10",
  "week_end": "2025-11-17",
  "points_earned_this_week": 200,
  "challenges_completed_this_week": 3,
  "total_points": 450,
  "total_challenges_completed": 5,
  "activity": [
    {
      "date": "2025-11-15",
      "challenges_completed": 2,
      "points_earned": 180
    }
  ]
}
```

---

### Custom Challenge Endpoints

#### GET /custom-challenges

Get all custom challenges created by teacher.

**Authentication:** Required (Teacher role)

**Response (200):**
```json
{
  "challenges": [
    {
      "id": 1,
      "title": "Advanced JOIN Exercise",
      "description": "Complex multi-table join",
      "dataset_id": 1,
      "expected_query": "SELECT ...",
      "points": 150,
      "created_at": "2025-11-17T10:00:00"
    }
  ]
}
```

---

#### POST /custom-challenges

Create a new custom challenge.

**Authentication:** Required (Teacher role)

**Request Body:**
```json
{
  "title": "Advanced JOIN Exercise",
  "description": "Practice multi-table joins",
  "dataset_id": 1,
  "expected_query": "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
  "points": 150,
  "difficulty": "hard"
}
```

**Response (201):**
```json
{
  "id": 1,
  "title": "Advanced JOIN Exercise",
  "description": "Practice multi-table joins",
  "dataset_id": 1,
  "expected_query": "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
  "points": 150,
  "difficulty": "hard",
  "created_by": 5,
  "created_at": "2025-11-17T10:00:00"
}
```

---

### Dataset Endpoints

#### GET /datasets

Get all available datasets.

**Authentication:** Required

**Response (200):**
```json
{
  "datasets": [
    {
      "id": 1,
      "name": "E-commerce Database",
      "description": "Users, orders, products",
      "schema": {
        "users": ["id", "name", "email"],
        "orders": ["id", "user_id", "total", "created_at"],
        "products": ["id", "name", "price"]
      },
      "created_at": "2025-11-17T10:00:00"
    }
  ]
}
```

---

## Rate Limiting

**Current Status:** Not implemented

**Future:** Planned rate limits per endpoint:
- Authentication: 5 requests per minute
- Challenge submission: 10 requests per minute
- General endpoints: 100 requests per minute

---

## API Clients

### JavaScript/TypeScript (Frontend)

```typescript
import ky from 'ky';

// Create configured client
const api = ky.create({
  prefixUrl: 'http://localhost:8000',
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
    ]
  }
});

// Example usage
const challenges = await api.get('challenges').json();
const result = await api.post('progress/submit', {
  json: {
    unit_id: 1,
    challenge_id: 1,
    query: 'SELECT * FROM users'
  }
}).json();
```

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "student@example.com",
    "password": "password"
})
data = response.json()
access_token = data["access_token"]

# Authenticated request
headers = {"Authorization": f"Bearer {access_token}"}
challenges = requests.get(f"{BASE_URL}/challenges", headers=headers).json()
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"password"}' \
  | jq -r '.access_token')

# Get challenges
curl -X GET http://localhost:8000/challenges \
  -H "Authorization: Bearer $TOKEN"
```

---

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - System architecture and design
- [Frontend Components](COMPONENTS.md) - UI component library
- [Contributing Guide](CONTRIBUTING.md) - Development workflow

---

*Last updated: 2025-11-17*
