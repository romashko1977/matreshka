"""
Matreshka - Secrets Vault Manager
Encrypted storage for API keys and sensitive credentials.
Keys are encrypted at rest and never exposed in plaintext via API.
"""
import os
import json
from typing import Optional, Dict
from cryptography.fernet import Fernet
from pathlib import Path


class SecretsManager:
    """Encrypted secrets storage for API keys."""

    VAULT_FILE = ".matreshka_vault.enc"
    CATEGORIES = ["exchanges", "telegram", "coinglass", "fpi", "ai_providers", "webhooks"]

    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or os.environ.get("MATRESHKA_SECRET_KEY", "")
        if len(self.encryption_key) < 32:
            # Pad to 32 bytes for Fernet key generation
            self.encryption_key = self.encryption_key.ljust(32, '0')[:32]
        import base64
        self._fernet = Fernet(base64.urlsafe_b64encode(self.encryption_key.encode()[:32]))
        self._secrets: Dict[str, Dict[str, str]] = {cat: {} for cat in self.CATEGORIES}
        self._load()

    def _load(self):
        """Load encrypted vault from disk."""
        path = Path(self.VAULT_FILE)
        if path.exists():
            try:
                encrypted = path.read_bytes()
                decrypted = self._fernet.decrypt(encrypted)
                self._secrets = json.loads(decrypted.decode())
            except Exception as e:
                print(f"Vault load error: {e}")

    def _save(self):
        """Save encrypted vault to disk."""
        try:
            data = json.dumps(self._secrets).encode()
            encrypted = self._fernet.encrypt(data)
            Path(self.VAULT_FILE).write_bytes(encrypted)
        except Exception as e:
            print(f"Vault save error: {e}")

    def set_secret(self, category: str, key: str, value: str):
        """Store a secret."""
        if category not in self._secrets:
            self._secrets[category] = {}
        self._secrets[category][key] = value
        self._save()

    def get_secret(self, category: str, key: str) -> Optional[str]:
        """Retrieve a secret."""
        return self._secrets.get(category, {}).get(key)

    def delete_secret(self, category: str, key: str):
        """Delete a secret."""
        if category in self._secrets and key in self._secrets[category]:
            del self._secrets[category][key]
            self._save()

    def get_masked(self, category: str) -> Dict[str, str]:
        """Get masked values for UI display (only show last 4 chars)."""
        result = {}
        for key, value in self._secrets.get(category, {}).items():
            if value and len(value) > 4:
                result[key] = "*" * (len(value) - 4) + value[-4:]
            elif value:
                result[key] = "****"
            else:
                result[key] = ""
        return result

    def get_all_masked(self) -> Dict[str, Dict[str, str]]:
        """Get all secrets masked for UI."""
        return {cat: self.get_masked(cat) for cat in self.CATEGORIES}

    def has_secret(self, category: str, key: str) -> bool:
        """Check if a secret exists."""
        return bool(self._secrets.get(category, {}).get(key))

    def get_connection_status(self) -> Dict[str, bool]:
        """Check which services have configured credentials."""
        return {
            "bybit": self.has_secret("exchanges", "bybit_api_key"),
            "mexc": self.has_secret("exchanges", "mexc_api_key"),
            "bitunix": self.has_secret("exchanges", "bitunix_api_key"),
            "binance": self.has_secret("exchanges", "binance_api_key"),
            "telegram": self.has_secret("telegram", "bot_token"),
            "coinglass": self.has_secret("coinglass", "api_key"),
            "fpi": self.has_secret("fpi", "api_key"),
            "openai": self.has_secret("ai_providers", "openai_api_key"),
            "anthropic": self.has_secret("ai_providers", "anthropic_api_key"),
        }
