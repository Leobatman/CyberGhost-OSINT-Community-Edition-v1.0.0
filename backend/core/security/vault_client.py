import os
import hvac
import structlog
from typing import Any, Dict

log = structlog.get_logger(__name__)

class VaultClient:
    """
    HashiCorp Vault Client for Secure Secret Management (V15.0 Enterprise)
    """
    def __init__(self):
        self.url = os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.token = os.getenv("VAULT_TOKEN", "root")
        self.client = hvac.Client(url=self.url, token=self.token)
        self.is_connected = False
        
        try:
            if self.client.is_authenticated():
                self.is_connected = True
                log.info("vault_connected", url=self.url)
            else:
                log.error("vault_auth_failed", url=self.url)
        except Exception as e:
            log.warning("vault_connection_failed", error=str(e), url=self.url)

    def get_secret(self, path: str, key: str) -> str | None:
        """Fetch a secret from Vault. Fallback to ENV if Vault is unreachable (Dev Mode)."""
        if self.is_connected:
            try:
                # Vault KV v2 paths usually have 'data'
                read_response = self.client.secrets.kv.v2.read_secret_version(path=path)
                return read_response['data']['data'].get(key)
            except hvac.exceptions.InvalidPath:
                log.warning("vault_secret_not_found", path=path, key=key)
            except Exception as e:
                log.error("vault_secret_error", path=path, error=str(e))
                
        # Dev fallback: try loading from environment variable mapping
        log.debug("vault_fallback_env", key=key)
        # Attempt to map path/key to a standard env var (e.g. cyberghost/database -> DB_PASSWORD)
        return os.getenv(key.upper())

    def write_secret(self, path: str, secrets: Dict[str, Any]) -> bool:
        """Write a dictionary of secrets to a path."""
        if self.is_connected:
            try:
                self.client.secrets.kv.v2.create_or_update_secret(path=path, secret=secrets)
                log.info("vault_secret_written", path=path)
                return True
            except Exception as e:
                log.error("vault_write_error", path=path, error=str(e))
        return False

# Singleton instance
vault = VaultClient()
