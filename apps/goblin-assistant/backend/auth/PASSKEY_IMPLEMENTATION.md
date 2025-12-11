# WebAuthn Passkey Implementation

## Overview

This implementation provides **full WebAuthn passkey verification** for passwordless authentication in the GoblinOS Assistant backend.

- ## Features

- ✅ **Complete WebAuthn Verification**

- Full cryptographic signature verification
- COSE public key parsing (ES256 algorithm)
- Authenticator data parsing and validation
- Client data JSON verification
- Challenge-response validation
- Origin validation

- ✅ **Security Features**

- Challenge-based authentication (one-time use)
- Challenge expiration (5 minutes)
- Automatic expired challenge cleanup
- Base64url encoding validation
- Credential ID matching
- Public key format validation

## API Endpoints


### 1. Request Challenge

```http
POST /auth/passkey/challenge
Content-Type: application/json

{
  "email": "user@example.com"  // Optional, for storing challenge
}
```

**Response:**

```json

{
  "challenge": "base64url-encoded-challenge"
}
```


### 2. Register Passkey

```http
POST /auth/passkey/register
Content-Type: application/json

{
  "email": "user@example.com",
  "credential_id": "base64url-encoded-credential-id",
  "public_key": "base64url-encoded-public-key-cose"
}
```

**Response:**

```json

{
  "message": "Passkey registered successfully"
}
```


### 3. Authenticate with Passkey

```http
POST /auth/passkey/auth
Content-Type: application/json

{
  "email": "user@example.com",

**Response:**
{
  "access_token": "jwt-token"
}
```

## Authentication Flow


### Registration Flow

1. User initiates registration from frontend
2. Frontend calls WebAuthn API (`navigator.credentials.create()`)
3. User authenticates with biometrics/security key
4. Frontend receives credential with public key
5. Frontend sends credential data to `/auth/passkey/register`
6. Backend validates and stores credential_id + public_key


### Client Authentication Flow

1. User requests challenge from `/auth/passkey/challenge` with email
2. Backend generates and stores challenge (expires in 5 min)
3. Frontend calls WebAuthn API (`navigator.credentials.get()`)
4. User authenticates with biometrics/security key
5. Frontend receives signed assertion
6. Frontend sends assertion to `/auth/passkey/auth`
7. Backend verifies:
   - Challenge exists and hasn't expired
   - Credential ID matches stored value
   - Origin matches expected value
   - Signature is valid using stored public key
   - Authenticator data is properly formatted
8. Backend returns JWT token on success

## Security Considerations


- ### ✅ Implemented

- Challenge-response protocol prevents replay attacks
- Challenges are single-use (deleted after verification)
- Challenges expire after 5 minutes
- Full cryptographic signature verification
- Origin validation prevents phishing
- Secure credential storage in database


- ### 🔄 Production Enhancements

- **Replace in-memory challenge store** with Redis or database
  - Current: `challenge_store = {}` (dict)
  - Production: Redis with TTL or database table
- **Add rate limiting** to prevent brute force
- **Add audit logging** for security events
- **Implement challenge cleanup worker** (periodic background task)
- **Add user-agent verification** for additional security
- **Support multiple passkeys per user**

## Implementation Details

### WebAuthn Verification (`passkeys.py`)

The `WebAuthnPasskey` class provides:

```python

# Challenge generation
generate_challenge() -> str
  Frontend integration examples (React/browser) are maintained in the canonical frontend docs: `apps/goblin-assistant/docs/PASSKEY_FRONTEND_INTEGRATION.md`. See the registration and authentication samples there for full examples and utility functions.
cleanup_expired_challenges()  # Removes expired challenges
```

## Environment Variables

```bash
# Frontend URL for origin validation
FRONTEND_URL=http://localhost:5173  # Development
FRONTEND_URL=https://app.example.com  # Production
```

## Frontend Integration Example

Frontend integration examples (React/browser) are maintained in the canonical frontend docs: `apps/goblin-assistant/docs/PASSKEY_FRONTEND_INTEGRATION.md`. See the registration and authentication samples there for full examples and utility functions.

## Testing

```bash

# Run passkey verification tests
pytest backend/auth/tests/test_passkeys.py -v

# Test with curl (after registration)
curl -X POST <http://localhost:8000/auth/passkey/challenge> \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Migration Notes

**From Demo to Production:**

1. ✅ **Removed:** Simplified verification that accepted any valid-looking data
2. ✅ **Added:** Full cryptographic verification with WebAuthn standards
3. ✅ **Added:** Challenge-response protocol
4. ✅ **Added:** Challenge expiration and cleanup
5. ✅ **Added:** Input validation for registration

- **Breaking Changes:**

- Passkey authentication now **requires a challenge** request first
- Challenges **expire after 5 minutes**
- Challenges are **single-use only**
- More strict validation on credential format

## References

- [WebAuthn Specification](https://www.w3.org/TR/webauthn-2/)
- [FIDO2 Overview](https://fidoalliance.org/fido2/)
- [MDN WebAuthn Guide](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API)

---

**Status:** ✅ Production-Ready (with recommended Redis/database for challenge store)
**Last Updated:** December 1, 2025
