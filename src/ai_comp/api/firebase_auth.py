from __future__ import annotations

from collections.abc import Mapping
from typing import Callable

from fastapi import Request


FirebaseTokenClaims = Mapping[str, object]
FirebaseTokenVerifier = Callable[[str], FirebaseTokenClaims | None]


class FirebaseIdTokenLearnerIdentityProvider:
    """Resolve a learner UID from a verified Firebase ID token.

    The Firebase Admin SDK verifier is injected so this boundary is testable
    without network calls or real Firebase credentials. A missing, malformed,
    unverified, or invalid token returns None and therefore fails closed.
    Unexpected verifier errors deliberately propagate so the API can distinguish
    an authentication infrastructure outage from an unauthenticated request.
    """

    def __init__(
        self,
        token_verifier: FirebaseTokenVerifier,
        *,
        require_verified_email: bool = True,
    ) -> None:
        self._token_verifier = token_verifier
        self._require_verified_email = require_verified_email

    def __call__(self, request: Request) -> str | None:
        authorization = request.headers.get("authorization", "")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].casefold() != "bearer":
            return None

        token = parts[1]
        if not token:
            return None

        claims = self._token_verifier(token)
        if not isinstance(claims, Mapping):
            return None

        uid = claims.get("uid")
        if (
            not isinstance(uid, str)
            or not uid
            or uid != uid.strip()
            or len(uid) > 128
        ):
            return None

        if self._require_verified_email and claims.get("email_verified") is not True:
            return None

        return uid


__all__ = [
    "FirebaseIdTokenLearnerIdentityProvider",
    "FirebaseTokenClaims",
    "FirebaseTokenVerifier",
]
