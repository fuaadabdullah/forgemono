"""
Test script to verify JWT authentication is working in the updated routers.
"""

import sys
from auth_service import get_auth_service
from auth.policies import UserRole


def test_jwt_auth():
    """Test JWT authentication functionality."""
    print("🔐 Testing JWT Authentication...")

    auth_service = get_auth_service()

    # Test creating a token
    try:
        token = auth_service.create_access_token(
            user_id="test-user-123",
            email="test@example.com",
            role=UserRole.USER,
            additional_scopes=[],
        )
        print("✅ Token creation successful")
        print(f"   Token: {token[:50]}...")

        # Test validating the token
        claims = auth_service.validate_access_token(token)
        if claims:
            print("✅ Token validation successful")
            print(f"   User ID: {claims.get('sub')}")
            print(f"   Email: {claims.get('email')}")
            print(f"   Role: {claims.get('role')}")

            # Test getting user scopes
            scopes = auth_service.get_user_scopes(claims)
            print(f"   Scopes: {[s.value for s in scopes]}")
        else:
            print("❌ Token validation failed")
            return False

    except Exception as e:
        print(f"❌ JWT auth test failed: {e}")
        return False

    print("🎉 JWT authentication test passed!")
    return True


def test_secrets_manager():
    """Test secrets manager functionality."""
    print("\n🔑 Testing Secrets Manager...")

    from auth.secrets_manager import get_secrets_manager

    secrets_manager = get_secrets_manager()

    # Test getting JWT secret (should work with fallback)
    try:
        jwt_secret = secrets_manager.get_jwt_secret_key()
        print(f"JWT secret type: {type(jwt_secret)}")
        print(f"JWT secret value: {repr(jwt_secret)}")

        if jwt_secret and isinstance(jwt_secret, str):
            print("✅ JWT secret retrieval successful")
            return True
        else:
            print("❌ JWT secret is not a valid string")
            return False
    except Exception as e:
        print(f"❌ Secrets manager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Running authentication system tests...\n")

    jwt_ok = test_jwt_auth()
    secrets_ok = test_secrets_manager()

    if jwt_ok and secrets_ok:
        print("\n✅ All authentication tests passed!")
        print("\n📋 Next steps:")
        print("1. Set up your secrets (Bitwarden/Vault/environment variables)")
        print("2. Test API endpoints with JWT tokens")
        print("3. Update remaining routers (api_router, stream_router, etc.)")
        print("4. Remove old authentication methods")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)
