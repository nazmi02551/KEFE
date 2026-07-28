from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminPrincipal,
    AdminRole,
    AdminSessionResolution,
    AdminSessionStatus,
    IssuedAdminSession,
)


class PostgresAdminSessionStore:
    """Opaque Admin session issuer, resolver and CSRF verifier."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def issue(
        self,
        *,
        admin_subject_id: UUID,
        authenticated_at: datetime,
        mfa_satisfied_at: datetime,
        expires_at: datetime,
    ) -> IssuedAdminSession:
        if expires_at <= authenticated_at:
            raise ValueError("Admin session expiry must be after authentication")

        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        session_id = uuid4()
        try:
            with self._engine.begin() as connection:
                subject_state = connection.execute(
                    text(
                        """
                        SELECT state
                        FROM admin_security.subject
                        WHERE id = :subject_id
                        FOR UPDATE
                        """
                    ),
                    {"subject_id": admin_subject_id},
                ).scalar_one_or_none()
                if subject_state != "ACTIVE":
                    raise ValueError("Admin subject is not active")

                connection.execute(
                    text(
                        """
                        INSERT INTO admin_security.session (
                            id,
                            subject_id,
                            token_hash,
                            csrf_token_hash,
                            authenticated_at,
                            mfa_satisfied_at,
                            expires_at,
                            last_seen_at
                        ) VALUES (
                            :id,
                            :subject_id,
                            :token_hash,
                            :csrf_token_hash,
                            :authenticated_at,
                            :mfa_satisfied_at,
                            :expires_at,
                            :last_seen_at
                        )
                        """
                    ),
                    {
                        "id": session_id,
                        "subject_id": admin_subject_id,
                        "token_hash": self._digest(session_token),
                        "csrf_token_hash": self._digest(csrf_token),
                        "authenticated_at": authenticated_at,
                        "mfa_satisfied_at": mfa_satisfied_at,
                        "expires_at": expires_at,
                        "last_seen_at": authenticated_at,
                    },
                )
        except IntegrityError as exc:
            raise ValueError("Admin session could not be issued") from exc

        return IssuedAdminSession(
            session_id=session_id,
            session_token=session_token,
            csrf_token=csrf_token,
            expires_at=expires_at,
        )

    def resolve(self, session_token: str) -> AdminSessionResolution:
        if not session_token:
            return AdminSessionResolution(AdminSessionStatus.INVALID)

        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        session.id,
                        session.subject_id,
                        session.authenticated_at,
                        session.mfa_satisfied_at,
                        session.step_up_at,
                        session.expires_at,
                        session.last_seen_at,
                        session.revoked_at,
                        subject.state AS subject_state,
                        now() AS database_now
                    FROM admin_security.session session
                    JOIN admin_security.subject subject
                      ON subject.id = session.subject_id
                    WHERE session.token_hash = :token_hash
                    """
                ),
                {"token_hash": self._digest(session_token)},
            ).mappings().one_or_none()
            if row is None:
                return AdminSessionResolution(AdminSessionStatus.INVALID)
            if row["revoked_at"] is not None or row["subject_state"] != "ACTIVE":
                return AdminSessionResolution(AdminSessionStatus.REVOKED)
            if row["expires_at"] <= row["database_now"]:
                return AdminSessionResolution(AdminSessionStatus.EXPIRED)

            roles = frozenset(
                AdminRole(value)
                for value in connection.execute(
                    text(
                        """
                        SELECT role
                        FROM admin_security.role_assignment
                        WHERE subject_id = :subject_id
                          AND revoked_at IS NULL
                        ORDER BY role
                        """
                    ),
                    {"subject_id": row["subject_id"]},
                ).scalars()
            )
            capabilities = frozenset(
                AdminCapability(value)
                for value in connection.execute(
                    text(
                        """
                        SELECT capability
                        FROM admin_security.capability_grant
                        WHERE subject_id = :subject_id
                          AND revoked_at IS NULL
                        ORDER BY capability
                        """
                    ),
                    {"subject_id": row["subject_id"]},
                ).scalars()
            )

        principal = AdminPrincipal(
            admin_subject_id=row["subject_id"],
            session_id=row["id"],
            roles=roles,
            direct_capabilities=capabilities,
            authenticated_at=row["authenticated_at"],
            mfa_satisfied_at=row["mfa_satisfied_at"],
            step_up_at=row["step_up_at"],
            expires_at=row["expires_at"],
            last_seen_at=row["last_seen_at"],
        )
        return AdminSessionResolution(AdminSessionStatus.ACTIVE, principal)

    def mark_seen(self, session_id: UUID, *, seen_at: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE admin_security.session
                    SET last_seen_at = GREATEST(last_seen_at, :seen_at)
                    WHERE id = :session_id
                      AND revoked_at IS NULL
                    """
                ),
                {"session_id": session_id, "seen_at": seen_at},
            )

    def verify(self, *, session_token: str, csrf_token: str) -> bool:
        if not session_token or not csrf_token:
            return False
        with self._engine.connect() as connection:
            stored_hash = connection.execute(
                text(
                    """
                    SELECT session.csrf_token_hash
                    FROM admin_security.session session
                    JOIN admin_security.subject subject
                      ON subject.id = session.subject_id
                    WHERE session.token_hash = :token_hash
                      AND session.revoked_at IS NULL
                      AND session.expires_at > now()
                      AND subject.state = 'ACTIVE'
                    """
                ),
                {"token_hash": self._digest(session_token)},
            ).scalar_one_or_none()
        return stored_hash is not None and hmac.compare_digest(
            stored_hash,
            self._digest(csrf_token),
        )

    def record_step_up(self, session_id: UUID, *, step_up_at: datetime) -> None:
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE admin_security.session
                    SET step_up_at = :step_up_at
                    WHERE id = :session_id
                      AND revoked_at IS NULL
                      AND expires_at > now()
                    """
                ),
                {"session_id": session_id, "step_up_at": step_up_at},
            )
            if result.rowcount != 1:
                raise ValueError("Active Admin session was not found")

    def revoke(self, session_id: UUID, *, revoked_at: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE admin_security.session
                    SET revoked_at = COALESCE(revoked_at, :revoked_at)
                    WHERE id = :session_id
                    """
                ),
                {"session_id": session_id, "revoked_at": revoked_at},
            )

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)
