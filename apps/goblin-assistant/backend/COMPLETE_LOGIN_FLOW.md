# Complete Login Flow - Usage Example

This demonstrates the complete JWT authentication flow for users to authenticate and receive tokens.

## API Endpoints

### 1. User Registration

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Response:**
```json

{
  "message": "User registered successfully",
  "user_id": "uuid-string"
}
```

### 2. User Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 3. Refresh Access Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 4. Get Current User Info

```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json

{
  "id": "uuid-string",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2025-12-09T...",
  "updated_at": "2025-12-09T..."
}
```

### 5. Logout

```http
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json

{
  "message": "Logged out successfully"
}
```

## Security Features

- **Password Hashing**: Uses bcrypt for secure password storage
- **JWT Tokens**: HS256 signed tokens with configurable secrets
- **Role-Based Access**: User roles determine available permissions
- **Token Refresh**: Long-lived refresh tokens for seamless authentication
- **Token Versioning**: Support for token revocation
- **Database Integration**: User validation against PostgreSQL database

## Client Usage Example

```javascript
// Register user
const registerResponse = await fetch('/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123',
    name: 'John Doe'
  })
});

// Login
const loginResponse = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123'
  })
});

const { access_token, refresh_token } = await loginResponse.json();

// Use access token for authenticated requests
const userResponse = await fetch('/auth/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

// Refresh token when needed
const refreshResponse = await fetch('/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token })
});
```

## Implementation Details

- **Registration**: Creates user with hashed password, assigns default USER role
- **Login**: Verifies credentials, returns JWT tokens with user info and scopes
- **Refresh**: Validates refresh token, returns new access token with current user data
- **User Info**: Returns current user profile from database using JWT subject
- **Logout**: Client-side token discard (stateless JWT implementation)

The complete login flow is now ready for production use! 🚀
