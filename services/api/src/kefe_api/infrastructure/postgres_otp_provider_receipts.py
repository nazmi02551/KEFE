from __future__ import annotations

from datetime import datetime

from sqlalchemy import Engine, text

from kefe_api.modules.identity.otp_provider_receipts import (
    OtpProviderReceipt,
    OtpProviderReceiptAppendResult,
    OtpProviderReceiptConflict,
    OtpProviderReceiptFacts,
    OtpProviderReceiptOutcome,
)


class PostgresOtpProviderReceiptRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append_and_prune(
        self,
        receipt: OtpProviderReceipt,
        *,
        prune_before: datetime,
    ) -> OtpProviderReceiptAppendResult:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM identity.otp_provider_receipt
                    WHERE received_at < :prune_before
                    """
                ),
                {"prune_before": prune_before},
            )
            result = connection.execute(
                text(
                    """
                    INSERT INTO identity.otp_provider_receipt (
                        provider_event_ref,
                        delivery_ref,
                        outcome,
                        occurred_at,
                        received_at
                    ) VALUES (
                        :provider_event_ref,
                        :delivery_ref,
                        :outcome,
                        :occurred_at,
                        :received_at
                    )
                    ON CONFLICT (provider_event_ref) DO NOTHING
                    """
                ),
                {
                    "provider_event_ref": receipt.provider_event_ref,
                    "delivery_ref": receipt.delivery_ref,
                    "outcome": receipt.outcome.value,
                    "occurred_at": receipt.occurred_at,
                    "received_at": receipt.received_at,
                },
            )
            if result.rowcount == 1:
                return OtpProviderReceiptAppendResult(receipt, duplicate=False)
            row = connection.execute(
                text(
                    """
                    SELECT
                        provider_event_ref,
                        delivery_ref,
                        outcome,
                        occurred_at,
                        received_at
                    FROM identity.otp_provider_receipt
                    WHERE provider_event_ref = :provider_event_ref
                    """
                ),
                {"provider_event_ref": receipt.provider_event_ref},
            ).mappings().one()

        existing = _receipt_from_row(row)
        if (
            existing.delivery_ref == receipt.delivery_ref
            and existing.outcome is receipt.outcome
            and existing.occurred_at == receipt.occurred_at
        ):
            return OtpProviderReceiptAppendResult(existing, duplicate=True)
        raise OtpProviderReceiptConflict()

    def read_facts(
        self,
        *,
        window_started_at: datetime,
        as_of: datetime,
        prune_before: datetime,
    ) -> OtpProviderReceiptFacts:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM identity.otp_provider_receipt
                    WHERE received_at < :prune_before
                    """
                ),
                {"prune_before": prune_before},
            )
            row = connection.execute(
                text(
                    """
                    SELECT
                        count(*)::integer AS total_count,
                        count(*) FILTER (
                            WHERE outcome = 'DELIVERED'
                        )::integer AS delivered_count,
                        count(*) FILTER (
                            WHERE outcome = 'UNDELIVERABLE'
                        )::integer AS undeliverable_count,
                        count(*) FILTER (
                            WHERE outcome = 'EXPIRED'
                        )::integer AS expired_count,
                        max(received_at) AS latest_received_at
                    FROM identity.otp_provider_receipt
                    WHERE received_at >= :window_started_at
                      AND received_at <= :as_of
                    """
                ),
                {
                    "window_started_at": window_started_at,
                    "as_of": as_of,
                },
            ).mappings().one()
        return OtpProviderReceiptFacts(
            as_of=as_of,
            window_started_at=window_started_at,
            total_count=int(row["total_count"]),
            delivered_count=int(row["delivered_count"]),
            undeliverable_count=int(row["undeliverable_count"]),
            expired_count=int(row["expired_count"]),
            latest_received_at=row["latest_received_at"],
        )


def _receipt_from_row(row) -> OtpProviderReceipt:
    return OtpProviderReceipt(
        provider_event_ref=str(row["provider_event_ref"]),
        delivery_ref=str(row["delivery_ref"]),
        outcome=OtpProviderReceiptOutcome(str(row["outcome"])),
        occurred_at=row["occurred_at"],
        received_at=row["received_at"],
    )


__all__ = ["PostgresOtpProviderReceiptRepository"]
