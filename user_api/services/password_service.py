import bcrypt

_BCRYPT_ROUNDS: int = 12


def hash_password(plain: str) -> str:
    """Return a bcrypt hash string for the given plaintext password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash.

    bcrypt.checkpw is constant-time — safe against timing attacks.
    Malformed hashes return False instead of propagating an exception.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False
