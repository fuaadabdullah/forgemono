import base64
import json
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from auth.passkeys import WebAuthnPasskey


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


@pytest.fixture
def client_with_db():
    import database
    import importlib

    backend_db = importlib.import_module("backend.database")
    from backend.database import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    # Import backend.models_base so models are registered against backend.database.Base
    import backend.models_base as models_base  # noqa: F401 (import to register models)
    import sys

    # Ensure top-level import names are aliases to backend.* modules so subsequent
    # imports use the same module objects and do not re-register tables.
    sys.modules["models_base"] = models_base
    sys.modules["backend.models_base"] = models_base
    # Alias the `database` module to the backend.database so both import paths
    # refer to the same module instance.
    import backend.database as backend_db_mod

    sys.modules["database"] = backend_db_mod
    sys.modules["backend.database"] = backend_db_mod

    # Create an in-memory SQLite DB to avoid filesystem issues and ensure isolation
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Ensure the module-level database engine and session are replaced so path
    # handlers and other modules that import database.SessionLocal use our test
    # engine/session.
    # NOTE: This mutates the in-memory module after it was already imported by
    # `auth.auth_router` during module import. That ensures the TestClient uses
    # the same engine/session used to create tables here.
    # Patch both top-level `database` module and `backend.database` (package) to the test engine/session
    database.engine = engine
    database.SessionLocal = TestingSessionLocal
    import importlib

    backend_db = importlib.import_module("backend.database")
    backend_db.engine = engine
    backend_db.SessionLocal = TestingSessionLocal
    # Create tables on the test engine using the models' Base metadata to ensure
    # tables are created for the same declarative base as the models.
    models_base.Base.metadata.create_all(bind=engine)

    # Verify table creation using a direct session
    session = TestingSessionLocal()
    try:
        # Perform a simple check query against app_users to ensure table exists
        from sqlalchemy import text

        session.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='app_users';"
            )
        )
        # (We don't assert here - if it fails, later queries will reveal problem)
    finally:
        session.close()

    # Import auth router after the test DB and tables are prepared to avoid duplicate model imports
    import importlib

    auth_router = importlib.import_module("auth.auth_router").router

    app = FastAPI()
    app.include_router(auth_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override both the canonical database.get_db and any function imported into
    # other modules (auth_router imports get_db directly) so the DI resolves to
    # our test session even if the router captured the function object earlier.
    # Override both `database.get_db` and `backend.database.get_db` for DI
    app.dependency_overrides[database.get_db] = override_get_db
    try:
        app.dependency_overrides[backend_db.get_db] = override_get_db
    except Exception:
        pass
    try:
        import importlib

        auth_router_module = importlib.import_module("auth.auth_router")
        if hasattr(auth_router_module, "get_db"):
            app.dependency_overrides[auth_router_module.get_db] = override_get_db
    except Exception:
        pass
    return TestClient(app)


def test_passkey_register_and_auth(monkeypatch, client_with_db):
    client = client_with_db

    email = "testpass@example.com"
    password = "secret123"

    # Ensure auth service has a JWT secret available in tests
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-tests")

    # Register user (password-based) first
    # Create user directly in test DB to avoid depending on the register endpoint
    from database import SessionLocal
    from models_base import User
    import bcrypt

    session = SessionLocal()
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(email=email, password_hash=pw_hash, name="Test User")
    session.add(user)
    session.commit()
    session.close()

    # Request challenge
    res = client.post("/auth/passkey/challenge", params={"email": email})
    assert res.status_code == 200
    challenge = res.json().get("challenge")
    assert challenge is not None

    # Create dummy credential id and public key (base64url)
    cred_id = b64url(b"credential-id-123")
    public_key = b64url(b"public-key-blob")

    # Register passkey
    res = client.post(
        "/auth/passkey/register",
        json={"email": email, "credential_id": cred_id, "public_key": public_key},
    )
    assert res.status_code == 200

    # Mock verification to avoid heavy crypto
    async def fake_verify(*args, **kwargs):
        return True

    monkeypatch.setattr(WebAuthnPasskey, "verify_passkey_authentication", fake_verify)

    # Prepare client_data_json with challenge base64url encoded
    client_data = {
        "challenge": b64url(challenge.encode()),
        "origin": "http://localhost:5173",
        "type": "webauthn.get",
    }
    client_data_b64 = b64url(json.dumps(client_data).encode("utf-8"))
    authenticator_data_b64 = b64url(b"authenticator-data")
    signature_b64 = b64url(b"signaturebytes")

    res = client.post(
        "/auth/passkey/auth",
        json={
            "email": email,
            "credential_id": cred_id,
            "authenticator_data": authenticator_data_b64,
            "client_data_json": client_data_b64,
            "signature": signature_b64,
        },
    )
    if res.status_code != 200:
        # Print the error body for debugging
        print("PASSKEY AUTH FAILED:", res.status_code, res.text)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
