#!/usr/bin/env python3
"""
Encryption Keys Generator for SQLCipher

Generates cryptographically secure encryption keys for database encryption.
Output is formatted for .env file configuration.

Usage:
    python scripts/generate_encryption_keys.py

Output:
    Displays DB_ENCRYPTION_KEY=<base64-encoded-32-bytes> ready to paste into .env
"""

import secrets
import base64
import sys
from pathlib import Path


def generate_encryption_key(key_size: int = 32) -> str:
    """
    Generate a cryptographically secure encryption key.

    Args:
        key_size: Size in bytes (32 bytes = 256 bits for AES-256)

    Returns:
        Base64-encoded key string
    """
    raw_key = secrets.token_bytes(key_size)
    encoded_key = base64.b64encode(raw_key).decode('utf-8')
    return encoded_key


def main():
    """Generate encryption keys and display output."""
    print("=" * 60)
    print("Encryption Keys Generator for SQLCipher")
    print("=" * 60)
    print()

    # Generate DB encryption key (AES-256: 32 bytes)
    db_key = generate_encryption_key(32)

    print("Database Encryption Key (AES-256):")
    print(f"DB_ENCRYPTION_KEY={db_key}")
    print()

    print("Instructions:")
    print("1. Copy the above line")
    print("2. Paste into backend/.env")
    print("3. Ensure backend/.env is in .gitignore (NEVER commit secrets!)")
    print()

    print("=" * 60)
    print("⚠️  SECURITY NOTES:")
    print("=" * 60)
    print("✅ Key is cryptographically secure (secrets.token_bytes)")
    print("✅ Key size: 32 bytes (256 bits) for AES-256")
    print("✅ NEVER commit this key to version control")
    print("✅ NEVER hardcode in application code")
    print("✅ For production: use AWS Secrets Manager or HashiCorp Vault")
    print("=" * 60)
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error generating encryption key: {e}", file=sys.stderr)
        sys.exit(1)
