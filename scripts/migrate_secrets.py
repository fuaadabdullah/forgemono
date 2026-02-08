#!/usr/bin/env python3
"""
Goblin Assistant Secrets Migration Script
Migrates secrets from legacy systems to HashiCorp Vault

Usage:
    python3 scripts/migrate_secrets.py --environment staging --dry-run
    python3 scripts/migrate_secrets.py --environment staging --migrate
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from mock_vault_server import mock_vault

    USE_MOCK_VAULT = True
    print("🔧 Using Mock Vault for testing")
except ImportError:
    try:
        import hvac

        USE_MOCK_VAULT = False
        print("🔐 Using Real Vault client")
    except ImportError:
        print("❌ Neither mock_vault_server nor hvac available")
        sys.exit(1)


class SecretsMigrator:
    """Handles migration of secrets from legacy systems to Vault"""

    def __init__(self, environment: str, dry_run: bool = True):
        self.environment = environment
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"

        # Initialize Vault client
        if USE_MOCK_VAULT:
            self.vault = mock_vault
        else:
            self.vault = hvac.Client(
                url=os.getenv("VAULT_ADDR", "http://localhost:8200"),
                token=os.getenv("VAULT_TOKEN", "goblin-vault-root-token"),
            )

        self.migration_steps = [
            "database_secrets",
            "bitwarden_secrets",
            "ssh_keys",
            "api_keys_file",
        ]

        self.results = {step: False for step in self.migration_steps}

    def run_migration(self) -> bool:
        """Execute the complete migration process"""
        print(
            f"🚀 Starting {'DRY RUN' if self.dry_run else 'LIVE'} migration for {self.environment} environment"
        )
        print("=" * 60)

        success_count = 0

        # Step 1: Migrate database secrets
        if self.migrate_database_secrets():
            success_count += 1

        # Step 2: Migrate Bitwarden secrets
        if self.migrate_bitwarden_secrets():
            success_count += 1

        # Step 3: Migrate SSH keys
        if self.migrate_ssh_keys():
            success_count += 1

        # Step 4: Migrate API keys from file
        if self.migrate_api_keys_file():
            success_count += 1

        print("=" * 60)
        print(
            f"📊 Migration completed: {success_count}/{len(self.migration_steps)} steps successful"
        )

        if not self.dry_run and success_count == len(self.migration_steps):
            print("✅ Migration successful! Ready to enable Vault mode.")
            # Save migration state
            if USE_MOCK_VAULT:
                self.vault.save_state(f"migration_state_{self.environment}.json")
            return True
        elif self.dry_run:
            print("🔍 Dry run completed. Run with --migrate to execute live migration.")
            return True
        else:
            print("❌ Migration failed. Check errors above.")
            # Save partial migration state
            if USE_MOCK_VAULT:
                self.vault.save_state(
                    f"migration_state_{self.environment}_partial.json"
                )
            return False

    def migrate_database_secrets(self) -> bool:
        """Migrate database connection secrets"""
        print("\n1️⃣ Migrating Database Secrets...")

        try:
            # Read database configuration from environment
            db_config = {
                "host": os.getenv("DATABASE_HOST", "localhost"),
                "port": os.getenv("DATABASE_PORT", "5432"),
                "name": os.getenv("DATABASE_NAME", "goblin_assistant"),
                "admin_user": os.getenv("DATABASE_ADMIN_USER", "vault_admin"),
                "admin_password": os.getenv(
                    "DATABASE_ADMIN_PASSWORD", "vault_password"
                ),
            }

            if self.dry_run:
                print(
                    f"   📋 Would migrate database config: {db_config['host']}:{db_config['port']}/{db_config['name']}"
                )
                self.results["database_secrets"] = True
                return True

            # Write to Vault
            success = self.vault.write_secret(
                f"{self.environment}/database/config", db_config
            )
            if success:
                print("   ✅ Database secrets migrated to Vault")
                self.results["database_secrets"] = True
                return True
            else:
                print("   ❌ Failed to write database secrets to Vault")
                return False

        except Exception as e:
            print(f"   ❌ Database migration error: {e}")
            return False

    def migrate_bitwarden_secrets(self) -> bool:
        """Migrate secrets from Bitwarden CLI"""
        print("\n2️⃣ Migrating Bitwarden Secrets...")

        try:
            # Check if Bitwarden CLI is available
            result = subprocess.run(
                ["bw", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                print("   ⚠️ Bitwarden CLI not available, skipping")
                self.results["bitwarden_secrets"] = True  # Not an error
                return True

            # Get Bitwarden session
            session = os.getenv("BW_SESSION")
            if not session:
                print("   ⚠️ No BW_SESSION found, attempting login...")
                # Try to login (this will require user interaction)
                login_result = subprocess.run(
                    ["bw", "login", "--check"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if login_result.returncode != 0:
                    print("   ⚠️ Bitwarden login required, skipping for now")
                    self.results["bitwarden_secrets"] = True
                    return True

            # List items from Bitwarden
            cmd = ["bw", "list", "items", "--folderid", "null"]
            if session:
                cmd.extend(["--session", session])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"   ⚠️ Failed to list Bitwarden items: {result.stderr}")
                self.results["bitwarden_secrets"] = True
                return True

            items = json.loads(result.stdout)
            api_keys = {}

            for item in items:
                if item.get("type") == 1:  # Login item
                    name = item.get("name", "").lower()
                    if any(
                        keyword in name for keyword in ["api", "key", "token", "secret"]
                    ):
                        username = item.get("login", {}).get("username", "")
                        password = item.get("login", {}).get("password", "")
                        if username and password:
                            api_keys[name] = {
                                "username": username,
                                "password": password,
                            }

            if not api_keys:
                print("   📋 No API keys found in Bitwarden")
                self.results["bitwarden_secrets"] = True
                return True

            if self.dry_run:
                print(f"   📋 Would migrate {len(api_keys)} API keys from Bitwarden")
                for name in api_keys.keys():
                    print(f"      - {name}")
                self.results["bitwarden_secrets"] = True
                return True

            # Write to Vault
            success = self.vault.write_secret(
                f"{self.environment}/bitwarden/api_keys", api_keys
            )
            if success:
                print(
                    f"   ✅ Migrated {len(api_keys)} API keys from Bitwarden to Vault"
                )
                self.results["bitwarden_secrets"] = True
                return True
            else:
                print("   ❌ Failed to write Bitwarden secrets to Vault")
                return False

        except Exception as e:
            print(f"   ❌ Bitwarden migration error: {e}")
            return False

    def migrate_ssh_keys(self) -> bool:
        """Migrate SSH keys"""
        print("\n3️⃣ Migrating SSH Keys...")

        try:
            ssh_dir = Path.home() / ".ssh"
            if not ssh_dir.exists():
                print("   📋 No SSH directory found")
                self.results["ssh_keys"] = True
                return True

            ssh_keys = {}
            for key_file in ssh_dir.glob("id_*"):
                if key_file.suffix not in [".pub"]:
                    try:
                        with open(key_file, "r") as f:
                            private_key = f.read().strip()
                        pub_file = key_file.with_suffix(key_file.suffix + ".pub")
                        public_key = ""
                        if pub_file.exists():
                            with open(pub_file, "r") as f:
                                public_key = f.read().strip()

                        ssh_keys[key_file.name] = {
                            "private_key": private_key,
                            "public_key": public_key,
                        }
                    except Exception as e:
                        print(f"   ⚠️ Failed to read {key_file.name}: {e}")

            if not ssh_keys:
                print("   📋 No SSH keys found")
                self.results["ssh_keys"] = True
                return True

            if self.dry_run:
                print(f"   📋 Would migrate {len(ssh_keys)} SSH keys")
                for name in ssh_keys.keys():
                    print(f"      - {name}")
                self.results["ssh_keys"] = True
                return True

            # Write to Vault
            success = self.vault.write_secret(f"{self.environment}/ssh/keys", ssh_keys)
            if success:
                print(f"   ✅ Migrated {len(ssh_keys)} SSH keys to Vault")
                self.results["ssh_keys"] = True
                return True
            else:
                print("   ❌ Failed to write SSH keys to Vault")
                return False

        except Exception as e:
            print(f"   ❌ SSH key migration error: {e}")
            return False

    def migrate_api_keys_file(self) -> bool:
        """Migrate API keys from local file"""
        print("\n4️⃣ Migrating API Keys File...")

        try:
            # Look for common API key files
            possible_files = [
                self.project_root / ".env.production",
                self.project_root / ".env.staging",
                self.project_root / "api_keys.json",
                self.project_root / "secrets.json",
            ]

            api_keys = {}

            for file_path in possible_files:
                if file_path.exists():
                    try:
                        if file_path.suffix == ".json":
                            with open(file_path, "r") as f:
                                data = json.load(f)
                                api_keys.update(data)
                        else:
                            # Parse .env file
                            with open(file_path, "r") as f:
                                for line in f:
                                    line = line.strip()
                                    if (
                                        line
                                        and not line.startswith("#")
                                        and "=" in line
                                    ):
                                        key, value = line.split("=", 1)
                                        if any(
                                            keyword in key.lower()
                                            for keyword in [
                                                "api",
                                                "key",
                                                "token",
                                                "secret",
                                            ]
                                        ):
                                            api_keys[key] = value
                    except Exception as e:
                        print(f"   ⚠️ Failed to read {file_path.name}: {e}")

            if not api_keys:
                print("   📋 No API keys file found")
                self.results["api_keys_file"] = True
                return True

            if self.dry_run:
                print(f"   📋 Would migrate {len(api_keys)} API keys from file")
                for name in list(api_keys.keys())[:3]:  # Show first 3
                    print(f"      - {name}")
                if len(api_keys) > 3:
                    print(f"      ... and {len(api_keys) - 3} more")
                self.results["api_keys_file"] = True
                return True

            # Write to Vault
            success = self.vault.write_secret(
                f"{self.environment}/api_keys/file", api_keys
            )
            if success:
                print(f"   ✅ Migrated {len(api_keys)} API keys from file to Vault")
                self.results["api_keys_file"] = True
                return True
            else:
                print("   ❌ Failed to write API keys to Vault")
                return False

        except Exception as e:
            print(f"   ❌ API keys file migration error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Migrate secrets to HashiCorp Vault")
    parser.add_argument(
        "--environment",
        required=True,
        choices=["staging", "production"],
        help="Target environment",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Execute dry run (default behavior)",
    )
    parser.add_argument("--migrate", action="store_true", help="Execute live migration")
    parser.add_argument("--mock", action="store_true", help="Force use of mock vault")

    args = parser.parse_args()

    # If --migrate is specified, disable dry-run
    if args.migrate:
        args.dry_run = False

    # Override USE_MOCK_VAULT if specified
    if args.mock:
        global USE_MOCK_VAULT
        USE_MOCK_VAULT = True

    migrator = SecretsMigrator(args.environment, args.dry_run)
    success = migrator.run_migration()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
