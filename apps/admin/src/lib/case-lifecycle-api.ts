export type CaseChangeType = "NONE" | "VERSION_SHIFT" | "INSTITUTION_RESPONSE";

export interface CaseLifecycleStatusResponse {
  case_id: string;
  current_case_version_id: string;
  version_number: number;
  is_published: boolean;
  has_institutional_response: boolean;
  update_summary: string;
  last_updated_at: string;
}

export interface SavedCaseQueryItem {
  case_id: string;
  saved_version_id: string;
}

export interface ReconciledCaseResult {
  case_id: string;
  saved_version_id: string;
  current_case_version_id: string;
  has_update: boolean;
  change_type: CaseChangeType;
  notification_label_tr: string;
  notification_label_en: string;
}

export interface ReconcileSavedCasesResponse {
  total_checked: number;
  updated_count: number;
  results: ReconciledCaseResult[];
  reconciled_at: string;
}

export class CaseLifecycleApiClient {
  private baseUrl: string;

  constructor(baseUrl = "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  async getCaseLifecycle(caseId: string): Promise<CaseLifecycleStatusResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(`${this.baseUrl}/v1/cases/${caseId}/lifecycle`);
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    return {
      case_id: caseId,
      current_case_version_id: `${caseId}_v2`,
      version_number: 2,
      is_published: true,
      has_institutional_response: true,
      update_summary: "Kurumsal resmi yanıt yayımlandı.",
      last_updated_at: new Date().toISOString(),
    };
  }

  async reconcileSavedCases(
    savedCases: SavedCaseQueryItem[]
  ): Promise<ReconcileSavedCasesResponse> {
    if (!savedCases || savedCases.length === 0) {
      throw new Error("savedCases array must not be empty");
    }

    if (this.baseUrl) {
      try {
        const res = await fetch(`${this.baseUrl}/v1/cases/reconcile-saved`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ saved_cases: savedCases }),
        });
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const results: ReconciledCaseResult[] = savedCases.map((item) => {
      const currentVersion = `${item.case_id}_v2`;
      const isShift = item.saved_version_id !== currentVersion;
      return {
        case_id: item.case_id,
        saved_version_id: item.saved_version_id,
        current_case_version_id: currentVersion,
        has_update: isShift,
        change_type: isShift ? "VERSION_SHIFT" : "NONE",
        notification_label_tr: isShift
          ? "Vaka yeni sürüme güncellendi"
          : "Değişiklik yok",
        notification_label_en: isShift
          ? "Case updated to a newer version"
          : "No updates",
      };
    });

    return {
      total_checked: savedCases.length,
      updated_count: results.filter((r) => r.has_update).length,
      results,
      reconciled_at: new Date().toISOString(),
    };
  }
}
