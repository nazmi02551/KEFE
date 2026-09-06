from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class IncentiveTypeEnum(StrEnum):
    FINANCIAL_PROFIT = "FINANCIAL_PROFIT"
    POLITICAL_ELECTORAL = "POLITICAL_ELECTORAL"
    BUREAUCRATIC_RISK_AVERSION = "BUREAUCRATIC_RISK_AVERSION"
    CIVIC_PUBLIC_WELFARE = "CIVIC_PUBLIC_WELFARE"


class AlignmentStatusEnum(StrEnum):
    ALIGNED = "ALIGNED"
    MISALIGNED = "MISALIGNED"
    PERVERSE = "PERVERSE"


class PerverseRiskEnum(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class IncentiveNodeItem:
    stakeholder_group: str
    core_incentive: str
    incentive_type: IncentiveTypeEnum
    alignment_status: AlignmentStatusEnum
    intensity_score: float
    unintended_behavior: str = ""

    def to_dict(self) -> dict:
        return {
            "stakeholder_group": self.stakeholder_group,
            "core_incentive": self.core_incentive,
            "incentive_type": self.incentive_type.value,
            "alignment_status": self.alignment_status.value,
            "intensity_score": round(self.intensity_score, 4),
            "unintended_behavior": self.unintended_behavior,
        }


@dataclass(frozen=True, slots=True)
class IncentiveMapResult:
    map_id: str
    case_version_id: UUID
    alignment_index: float
    perverse_incentive_risk: PerverseRiskEnum
    primary_driver: str
    mitigation_mechanism: str
    incentive_nodes: list[IncentiveNodeItem]

    def to_dict(self) -> dict:
        return {
            "map_id": self.map_id,
            "case_version_id": str(self.case_version_id),
            "alignment_index": round(self.alignment_index, 4),
            "perverse_incentive_risk": self.perverse_incentive_risk.value,
            "primary_driver": self.primary_driver,
            "mitigation_mechanism": self.mitigation_mechanism,
            "incentive_nodes": [n.to_dict() for n in self.incentive_nodes],
        }


class IncentiveMapCalculator:
    @staticmethod
    def analyze(
        *,
        map_id: str,
        case_version_id: UUID,
        alignment_index: float,
        perverse_incentive_risk: PerverseRiskEnum,
        primary_driver: str,
        mitigation_mechanism: str,
        incentive_nodes: list[IncentiveNodeItem],
    ) -> IncentiveMapResult:
        if not 0.0 <= alignment_index <= 1.0:
            raise ValueError(f"alignment_index must be in [0.0, 1.0], got {alignment_index}")
        if len(primary_driver.strip()) < 3:
            raise ValueError("primary_driver must have at least 3 characters")
        if len(mitigation_mechanism.strip()) < 3:
            raise ValueError("mitigation_mechanism must have at least 3 characters")
        if not incentive_nodes:
            raise ValueError("incentive_nodes cannot be empty")

        for node in incentive_nodes:
            if not 0.0 <= node.intensity_score <= 1.0:
                raise ValueError(
                    f"intensity_score must be in [0.0, 1.0], got {node.intensity_score}"
                )

        return IncentiveMapResult(
            map_id=map_id.strip(),
            case_version_id=case_version_id,
            alignment_index=alignment_index,
            perverse_incentive_risk=perverse_incentive_risk,
            primary_driver=primary_driver.strip(),
            mitigation_mechanism=mitigation_mechanism.strip(),
            incentive_nodes=incentive_nodes,
        )

    @classmethod
    def compute_for_case(cls, case_version_id: UUID) -> IncentiveMapResult:
        """Deterministic systemic incentive map for a case."""
        nodes = [
            IncentiveNodeItem(
                stakeholder_group="Özel Sektör / Hizmet Sağlayıcılar",
                core_incentive="Kısa vadeli işletme kârı ve pazar hakimiyetini koruma",
                incentive_type=IncentiveTypeEnum.FINANCIAL_PROFIT,
                alignment_status=AlignmentStatusEnum.MISALIGNED,
                intensity_score=0.85,
                unintended_behavior="Maliyetleri dışsallaştırarak kamuya yükleme eğilimi.",
            ),
            IncentiveNodeItem(
                stakeholder_group="Siyasi Karar Alıcılar",
                core_incentive="Seçim dönemi popülerliği ve anket desteğini maksimize etme",
                incentive_type=IncentiveTypeEnum.POLITICAL_ELECTORAL,
                alignment_status=AlignmentStatusEnum.PERVERSE,
                intensity_score=0.75,
                unintended_behavior="Gelecek nesillere mali ve ekolojik borç bırakma pahasına günü kurtarma.",
            ),
            IncentiveNodeItem(
                stakeholder_group="Kamu Düzenleyicisi ve Bürokrasi",
                core_incentive="İdari ihtilaflardan kaçınma ve bütçe güvencesi sağlama",
                incentive_type=IncentiveTypeEnum.BUREAUCRATIC_RISK_AVERSION,
                alignment_status=AlignmentStatusEnum.MISALIGNED,
                intensity_score=0.60,
                unintended_behavior="Statükoyu koruma ve proaktif denetim yerine reaktif kalma.",
            ),
            IncentiveNodeItem(
                stakeholder_group="Yurttaşlar ve Gelecek Nesiller",
                core_incentive="Erişilebilir, güvenli, adil ve sürdürülebilir kamu hizmeti",
                incentive_type=IncentiveTypeEnum.CIVIC_PUBLIC_WELFARE,
                alignment_status=AlignmentStatusEnum.ALIGNED,
                intensity_score=0.90,
                unintended_behavior="Kısa vadeli tüketici fiyat duyarlılığı ile uzun vadeli kamu yararı ikilemi.",
            ),
        ]

        return cls.analyze(
            map_id=f"INC-{case_version_id.hex[:8]}",
            case_version_id=case_version_id,
            alignment_index=0.62,
            perverse_incentive_risk=PerverseRiskEnum.MODERATE,
            primary_driver="Kısa Vadeli Kâr ve Seçim Odaklı Teşvik Dinamikleri",
            mitigation_mechanism="Bağımsız performans denetimi, şeffaflık zorunluluğu ve uzun vadeli etki tavanı",
            incentive_nodes=nodes,
        )
