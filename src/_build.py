"""Build-time configuration constants for Boltools.

Generated during build/packaging.
In release binaries, IS_RELEASE is strictly True and ignores BOLTOOLS_DEV overrides.
"""

IS_RELEASE: bool = False
BUILD_MIN_SEQUENCE: int = 1
APP_VERSION: str = "1.0.0"

# Public keys embedded in app binary for Ed25519 manifest verification.
# Allows dual keys for zero-downtime key rotation.
# Formatted as hex-encoded 32-byte Ed25519 public keys.
EMBEDDED_PUBLIC_KEYS = {
    # Key 1: Primary release key
    "key_1": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
    # Key 2: Secondary / Backup rotation key
    "key_2": ""
}
