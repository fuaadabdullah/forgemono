"""
Vault Client for Goblin Assistant
Handles secrets management migration from Fernet encryption to HashiCorp Vault
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager

try:
    import hvac
except ImportError:
    hvac = None

logger = logging.getLogger(__name__)


class VaultClient:
    """Client for interacting with HashiCorp Vault"""

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        token: Optional[str] = None,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_cert: Optional[str] = None,
        namespace: Optional[str] = None,
    ):
        """
        Initialize Vault client with multiple authentication methods.

        Args:
            vault_addr: Vault server address
            token: Vault token for authentication
            cert_path: Path to client certificate for mTLS auth
            key_path: Path to client key for mTLS auth
            ca_cert: Path to CA certificate
            namespace: Vault namespace (Enterprise only)
        """
        if hvac is None:
            raise ImportError(
                "hvac package is required for Vault client. Install with: pip install hvac"
            )

        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_cert = ca_cert
        self.namespace = namespace

        # Initialize client
        self.client = hvac.Client(
            url=self.vault_addr,
            token=self.token,
            cert=(self.cert_path, self.key_path)
            if self.cert_path and self.key_path
            else None,
            verify=self.ca_cert if self.ca_cert else True,
            namespace=self.namespace,
        )

        # Test connection
        if not self.client.is_authenticated():
            raise ValueError("Failed to authenticate with Vault")

    @classmethod
    def from_token(
        cls, vault_addr: Optional[str] = None, token: Optional[str] = None
    ) -> "VaultClient":
        """Create client using token authentication"""
        return cls(vault_addr=vault_addr, token=token)

    @classmethod
    def from_cert(
        cls,
        vault_addr: Optional[str] = None,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_cert: Optional[str] = None,
    ) -> "VaultClient":
        """Create client using certificate authentication"""
        return cls(
            vault_addr=vault_addr,
            cert_path=cert_path,
            key_path=key_path,
            ca_cert=ca_cert,
        )

    @classmethod
    def from_oidc(
        cls, vault_addr: Optional[str] = None, role: str = "goblin-assistant-app"
    ) -> "VaultClient":
        """Create client using OIDC authentication (for CI/CD)"""
        if hvac is None:
            raise ImportError("hvac package is required")

        client = hvac.Client(url=vault_addr or os.getenv("VAULT_ADDR"))
        auth_response = client.auth.jwt.jwt_login(
            role=role, jwt=os.getenv("VAULT_OIDC_TOKEN")
        )
        token = auth_response["auth"]["client_token"]

        return cls(vault_addr=vault_addr, token=token)

    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        try:
            return self.client.is_authenticated()
        except Exception:
            return False

    def get_secret(
        self, path: str, key: Optional[str] = None, mount_point: str = "secret"
    ) -> Union[str, Dict[str, Any]]:
        """
        Retrieve secret from KV store

        Args:
            path: Secret path
            key: Specific key to retrieve (returns dict if None)
            mount_point: KV mount point

        Returns:
            Secret value or full secret data
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount_point
            )

            data = response["data"]["data"]

            if key:
                return data.get(key, "")
            return data

        except Exception as e:
            logger.error(f"Failed to read secret {path}: {e}")
            return {} if not key else ""

    def set_secret(
        self, path: str, data: Dict[str, Any], mount_point: str = "secret"
    ) -> bool:
        """
        Store secret in KV store

        Args:
            path: Secret path
            data: Secret data dictionary
            mount_point: KV mount point

        Returns:
            Success status
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path, secret=data, mount_point=mount_point
            )
            return True
        except Exception as e:
            logger.error(f"Failed to write secret {path}: {e}")
            return False

    def get_database_credentials(
        self, role: str = "goblin-assistant-app"
    ) -> Dict[str, str]:
        """
        Get dynamic database credentials

        Args:
            role: Database role name

        Returns:
            Database credentials dict
        """
        try:
            response = self.client.secrets.database.generate_credentials(
                name=role, mount_point="database"
            )

            return {
                "username": response["data"]["username"],
                "password": response["data"]["password"],
            }
        except Exception as e:
            logger.error(f"Failed to get database credentials for role {role}: {e}")
            return {}

    def list_secrets(self, path: str = "", mount_point: str = "secret") -> list:
        """
        List secrets at path

        Args:
            path: Path to list
            mount_point: KV mount point

        Returns:
            List of secret keys
        """
        try:
            response = self.client.secrets.kv.v2.list_secrets_version(
                path=path, mount_point=mount_point
            )
            return response.get("data", {}).get("keys", [])
        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {e}")
            return []

    def delete_secret(self, path: str, mount_point: str = "secret") -> bool:
        """
        Delete secret from KV store

        Args:
            path: Secret path
            mount_point: KV mount point

        Returns:
            Success status
        """
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path, mount_point=mount_point
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            return False


class VaultSecretsManager:
    """Secrets manager that migrates from Fernet to Vault"""

    def __init__(self, vault_client: Optional[VaultClient] = None):
        """
        Initialize secrets manager

        Args:
            vault_client: Vault client instance (creates one if None)
        """
        self.vault = vault_client or self._create_vault_client()
        self.fallback_mode = False

        # Try to enable fallback mode if Vault is unavailable
        if not self.vault or not self.vault.is_authenticated():
            logger.warning("Vault unavailable, enabling fallback mode")
            self.fallback_mode = True

    def _create_vault_client(self) -> Optional[VaultClient]:
        """Create Vault client based on available authentication"""
        try:
            # Try token auth first (for development/testing)
            if os.getenv("VAULT_TOKEN"):
                return VaultClient.from_token()

            # Try OIDC auth (for CI/CD)
            if os.getenv("VAULT_OIDC_TOKEN"):
                return VaultClient.from_oidc()

            # Try certificate auth (for production services)
            cert_path = os.getenv("VAULT_CLIENT_CERT")
            key_path = os.getenv("VAULT_CLIENT_KEY")
            if cert_path and key_path:
                return VaultClient.from_cert(
                    cert_path=cert_path,
                    key_path=key_path,
                    ca_cert=os.getenv("VAULT_CA_CERT"),
                )

            logger.warning("No Vault authentication method available")
            return None

        except Exception as e:
            logger.error(f"Failed to create Vault client: {e}")
            return None

    def get_api_key(self, provider: str, key_type: str = "api_key") -> Optional[str]:
        """
        Get API key for provider

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            key_type: Key type ('api_key', 'secret_key', etc.)

        Returns:
            API key or None if not found
        """
        if self.fallback_mode:
            return self._get_fallback_api_key(provider, key_type)

        path = f"staging/api-keys/{provider}"
        secret = self.vault.get_secret(path)

        if isinstance(secret, dict):
            return secret.get(key_type)
        return None

    def set_api_key(
        self, provider: str, api_key: str, key_type: str = "api_key"
    ) -> bool:
        """
        Store API key for provider

        Args:
            provider: Provider name
            api_key: API key value
            key_type: Key type

        Returns:
            Success status
        """
        if self.fallback_mode:
            return self._set_fallback_api_key(provider, api_key, key_type)

        path = f"staging/api-keys/{provider}"
        data = {key_type: api_key}
        return self.vault.set_secret(path, data)

    def get_database_config(self) -> Dict[str, str]:
        """
        Get database configuration

        Returns:
            Database configuration dict
        """
        if self.fallback_mode:
            return self._get_fallback_database_config()

        # Try dynamic credentials first
        creds = self.vault.get_database_credentials("goblin-assistant-app")
        if creds:
            return creds

        # Fallback to static config
        config = self.vault.get_secret("staging/config/database")
        if isinstance(config, dict):
            return config

        return {}

    def _get_fallback_api_key(self, provider: str, key_type: str) -> Optional[str]:
        """Fallback method using environment variables"""
        env_key = f"{provider.upper()}_{key_type.upper()}"
        return os.getenv(env_key)

    def _set_fallback_api_key(self, provider: str, api_key: str, key_type: str) -> bool:
        """Fallback method - just logs (can't actually set env vars)"""
        logger.warning(
            f"Fallback mode: Would set {provider} {key_type} (not persisted)"
        )
        return False

    def _get_fallback_database_config(self) -> Dict[str, str]:
        """Fallback method using environment variables"""
        return {
            "username": os.getenv("DB_USERNAME", ""),
            "password": os.getenv("DB_PASSWORD", ""),
            "host": os.getenv("DB_HOST", ""),
            "database": os.getenv("DB_NAME", ""),
        }


# Global instance for easy access
_vault_manager: Optional[VaultSecretsManager] = None


def get_vault_manager() -> VaultSecretsManager:
    """Get global Vault secrets manager instance"""
    global _vault_manager
    if _vault_manager is None:
        _vault_manager = VaultSecretsManager()
    return _vault_manager


@contextmanager
def vault_session():
    """Context manager for Vault operations"""
    manager = get_vault_manager()
    try:
        yield manager
    except Exception as e:
        logger.error(f"Vault operation failed: {e}")
        raise
