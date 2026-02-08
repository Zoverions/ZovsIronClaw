import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from cryptography.fernet import Fernet

logger = logging.getLogger("GCA.SecureStorage")

class SecureStorage:
    """
    Manages encrypted storage for sensitive personalization files.
    Uses Fernet (AES-128-CBC + HMAC-SHA256) for authenticated encryption.
    """

    def __init__(self, key_path: Optional[Path] = None):
        """
        Initialize SecureStorage with a key file.
        If the key file doesn't exist, it will be generated.

        Args:
            key_path: Path to the encryption key file. Defaults to ~/.ironclaw/secure/key.bin
        """
        if key_path is None:
            # Default to user home directory
            home = Path.home()
            self.key_dir = home / ".ironclaw" / "secure"
            self.key_file = self.key_dir / "key.bin"
        else:
            self.key_file = Path(key_path)
            self.key_dir = self.key_file.parent

        self._ensure_key()
        try:
            with open(self.key_file, "rb") as f:
                key = f.read()
            self.cipher = Fernet(key)
            logger.info(f"SecureStorage initialized with key at {self.key_file}")
        except Exception as e:
            logger.error(f"Failed to load encryption key: {e}")
            raise

    def _ensure_key(self):
        """Generate and save a key if it doesn't exist."""
        if not self.key_file.exists():
            logger.info("Generating new encryption key...")
            self.key_dir.mkdir(parents=True, exist_ok=True)

            key = Fernet.generate_key()

            # Write with restricted permissions (600)
            try:
                # Create file with 600 permissions immediately
                fd = os.open(self.key_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, 'wb') as f:
                    f.write(key)
                logger.info(f"New key saved to {self.key_file}")
            except Exception as e:
                logger.error(f"Failed to save key: {e}")
                raise

    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt raw bytes."""
        return self.cipher.encrypt(data)

    def decrypt_data(self, token: bytes) -> bytes:
        """Decrypt raw bytes."""
        return self.cipher.decrypt(token)

    def append_jsonl(self, file_path: Path, data: Dict[str, Any]):
        """
        Append a dictionary as an encrypted JSON line to a file.
        Each line is a base64-encoded encrypted string.
        """
        try:
            json_str = json.dumps(data)
            encrypted = self.encrypt_data(json_str.encode("utf-8"))

            # Append as a line
            with open(file_path, "ab") as f:
                f.write(encrypted + b"\n")

        except Exception as e:
            logger.error(f"Failed to append encrypted data to {file_path}: {e}")
            raise

    def load_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load and decrypt all lines from an encrypted JSONL file.
        """
        if not file_path.exists():
            return []

        results = []
        try:
            with open(file_path, "rb") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        decrypted = self.decrypt_data(line)
                        obj = json.loads(decrypted.decode("utf-8"))
                        results.append(obj)
                    except Exception as e:
                        logger.warning(f"Failed to decrypt line in {file_path}: {e}")
                        continue
            return results
        except Exception as e:
            logger.error(f"Failed to read encrypted file {file_path}: {e}")
            return []

    def save_json(self, file_path: Path, data: Dict[str, Any]):
        """
        Save a dictionary as a fully encrypted file (not line-based).
        Overwrites the file.
        """
        try:
            json_str = json.dumps(data, indent=2)
            encrypted = self.encrypt_data(json_str.encode("utf-8"))

            with open(file_path, "wb") as f:
                f.write(encrypted)
            logger.debug(f"Saved encrypted state to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save encrypted file {file_path}: {e}")
            raise

    def load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt a fully encrypted JSON file.
        """
        if not file_path.exists():
            return None

        try:
            with open(file_path, "rb") as f:
                encrypted = f.read()

            decrypted = self.decrypt_data(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to load encrypted file {file_path}: {e}")
            return None
