"""Build-time configuration constants for Boltools.

Generated during build/packaging.
In release binaries, IS_RELEASE is strictly True and ignores BOLTOOLS_DEV overrides.
"""

IS_RELEASE: bool = False
BUILD_MIN_SEQUENCE: int = 1
APP_VERSION: str = "1.1.4"

# Public keys embedded in app binary for Ed25519 manifest verification.
# Allows dual keys for zero-downtime key rotation.
# Formatted as hex-encoded 32-byte Ed25519 public keys.
EMBEDDED_PUBLIC_KEYS = {
    # Key 1: Primary release key
    "key_1": "b4a6b85925c014b262e6a9a7be7b951e387f48d8f489ba76c564ed06f924e9a1",
    # Key 2: Secondary / Backup rotation key
    "key_2": ""
}
