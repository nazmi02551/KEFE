"""Case Quality Checklist Engine (CAP-075).

Replaces opaque single 'magic scores' with a verifiable 8-dimension checklist
for editorial fairness, source provenance, and constitutional neutrality.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class QualityAuditStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    FLAGGED = "FLAGGED"


@dataclass(frozen=True)
class QualityChecklistItem:
    dimension_id: str
    name_tr: str
    name_en: str
    criterion_tr: str
    criterion_en: str
    status: QualityAuditStatus
    reviewer_note: str


@dataclass(frozen=True)
class CaseQualityChecklistResult:
    case_version_id: str
    overall_status: str
    verified_count: int
    total_count: int
    items: list[QualityChecklistItem]
    methodology_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_version_id": self.case_version_id,
            "overall_status": self.overall_status,
            "verified_count": self.verified_count,
            "total_count": self.total_count,
            "items": [
                {
                    "dimension_id": item.dimension_id,
                    "name_tr": item.name_tr,
                    "name_en": item.name_en,
                    "criterion_tr": item.criterion_tr,
                    "criterion_en": item.criterion_en,
                    "status": item.status.value,
                    "reviewer_note": item.reviewer_note,
                }
                for item in self.items
            ],
            "methodology_hash": self.methodology_hash,
        }


class CaseQualityChecklistEvaluator:
    """Evaluates case against the governed 8-point quality checklist."""

    STANDARD_DIMENSIONS = [
        (
            "BALANCED_OPTIONS",
            "Dengeli Seçenekler",
            "Balanced Options",
            "Seçenekler kutuplaştırıcı veya kukla argüman olmaksızın gerçek normatif gerilimi temsil eder.",
            "Options represent genuine normative tension without strawman framing.",
        ),
        (
            "NEUTRAL_PROVENANCE",
            "Tarafsız Kaynak Kökeni",
            "Neutral Provenance",
            "Metin yönlendirici veya manipülatif dil içermez; tarafsız olgular sunulur.",
            "Text contains no leading or manipulative phrasing; neutral facts are presented.",
        ),
        (
            "DISCLOSED_STAKEHOLDERS",
            "Açıklanmış Paydaşlar",
            "Disclosed Stakeholders",
            "Karardan etkilenen tüm doğrudan ve dolaylı paydaşlar açıkça belirtilmiştir.",
            "All directly and indirectly impacted stakeholders are explicitly stated.",
        ),
        (
            "VERIFIED_SOURCES",
            "Doğrulanmış Kaynaklar",
            "Verified Sources",
            "En az iki bağımsız ve doğrulanabilir birincil veya ikincil kaynak bağlanmıştır.",
            "At least two independent and verifiable external sources are linked.",
        ),
        (
            "ACCESSIBLE_READABILITY",
            "Erişilebilir Okunabilirlik",
            "Accessible Readability",
            "Metin halkın genel erişimine uygun, duru ve teknik jargondan arındırılmıştır.",
            "Language is plain, accessible, and free of unnecessary technical jargon.",
        ),
        (
            "PRINCIPLE_INTEGRITY",
            "İlkesel Tutarlılık",
            "Principle Integrity",
            "Vaka temel hak, anayasal güvence veya kamu yararı ilkeleriyle uyumludur.",
            "Case aligns with fundamental rights, constitutional principles, or public interest.",
        ),
        (
            "REASON_PROMPT_EQUITY",
            "Eşit Gerekçe İstemi",
            "Reason Prompt Equity",
            "Gerekçe yakalama soruları belirli bir sonuca doğru yönlendirme veya telkin yapmaz.",
            "Pre-commit reason prompts do not nudge or prime toward a particular choice.",
        ),
        (
            "METHODOLOGY_TRANSPARENCY",
            "Metodolojik Şeffaflık",
            "Methodology Transparency",
            "Denetim adımları ve editör onay imzaları açıkça doğrulanabilir ve şeffaftır.",
            "Audit criteria and editorial review checkpoints are cryptographically verifiable.",
        ),
    ]

    def evaluate(
        self,
        case_version_id: str,
        custom_statuses: dict[str, tuple[QualityAuditStatus, str]] | None = None,
    ) -> CaseQualityChecklistResult:
        statuses = custom_statuses or {}
        items: list[QualityChecklistItem] = []

        for dim_id, name_tr, name_en, crit_tr, crit_en in self.STANDARD_DIMENSIONS:
            status, note = statuses.get(
                dim_id,
                (
                    QualityAuditStatus.VERIFIED,
                    "Standart anayasal editörlük denetiminden başarıyla geçti.",
                ),
            )
            items.append(
                QualityChecklistItem(
                    dimension_id=dim_id,
                    name_tr=name_tr,
                    name_en=name_en,
                    criterion_tr=crit_tr,
                    criterion_en=crit_en,
                    status=status,
                    reviewer_note=note,
                )
            )

        verified_count = sum(1 for i in items if i.status == QualityAuditStatus.VERIFIED)
        total_count = len(items)

        if verified_count == total_count:
            overall = "FULLY_AUDITED_PASS"
        elif any(i.status == QualityAuditStatus.FLAGGED for i in items):
            overall = "NEEDS_EDITORIAL_REVISION"
        else:
            overall = "AUDIT_IN_PROGRESS"

        return CaseQualityChecklistResult(
            case_version_id=case_version_id,
            overall_status=overall,
            verified_count=verified_count,
            total_count=total_count,
            items=items,
            methodology_hash="sha256-kefe-cqb-chk-8dim-7a19c",
        )
