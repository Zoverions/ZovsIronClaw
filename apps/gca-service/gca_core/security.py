"""
GCA Security Core
Handles mnemonic generation, key derivation, and message signing for the Mesh.
Ensures secure communication between nodes and "computer use" authorization.
"""

import os
import json
import base64
import logging
from typing import Tuple, Optional
from mnemonic import Mnemonic
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger("GCA.Security")

class SecurityManager:
    def __init__(self, key_path: str = None):
        self.mnemo = Mnemonic("english")
        self.private_key: Optional[ed25519.Ed25519PrivateKey] = None
        self.public_key: Optional[ed25519.Ed25519PublicKey] = None

        # If key_path provided, try to load existing key
        if key_path and os.path.exists(key_path):
            self.load_keys(key_path)

    def generate_passphrase(self) -> str:
        """Generate a new 12-word BIP39 mnemonic."""
        return self.mnemo.generate(strength=128)

    def derive_keys(self, passphrase: str) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Derive Ed25519 keypair from the passphrase (deterministically)."""
        seed = self.mnemo.to_seed(passphrase, passphrase="") # 64 bytes
        # Ed25519 keys are 32 bytes. We use the first 32 bytes of the seed.
        private_key_bytes = seed[:32]

        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        self.public_key = self.private_key.public_key()

        return self.private_key, self.public_key

    def sign_message(self, message: str) -> str:
        """Sign a message string and return base64 encoded signature."""
        if not self.private_key:
            raise ValueError("No private key loaded.")

        signature = self.private_key.sign(message.encode('utf-8'))
        return base64.b64encode(signature).decode('utf-8')

    def verify_signature(self, message: str, signature_b64: str, public_key_bytes: bytes = None) -> bool:
        """Verify a signature. If public_key_bytes not provided, uses own public key (self-verification test)."""
        try:
            signature = base64.b64decode(signature_b64)
            key = self.public_key

            if public_key_bytes:
                key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)

            if not key:
                 raise ValueError("No public key available for verification.")

            key.verify(signature, message.encode('utf-8'))
            return True
        except Exception as e:
            logger.debug(f"Signature verification failed: {e}")
            return False

    def get_public_key_b64(self) -> str:
        """Return public key as base64 string for sharing."""
        if not self.public_key:
            return ""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return base64.b64encode(pub_bytes).decode('utf-8')

    def get_wallet_address(self) -> str:
        """Return the wallet address (public key base64)."""
        return self.get_public_key_b64()

    def save_keys(self, path: str):
        """Save the private key to a file (encrypted/protected ideally, currently PEM)."""
        # In a real production scenario, this should use OS keychain or encryption.
        # For this implementation, we save as PEM with restrictive permissions.
        if not self.private_key:
            return

        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        with open(path, "wb") as f:
            f.write(pem)
        os.chmod(path, 0o600) # Read/Write for owner only

    def load_keys(self, path: str):
        """Load private key from file."""
        with open(path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
            self.public_key = self.private_key.public_key()
