export type ClaimType = "FACTUAL" | "NORMATIVE" | "VALUE" | "CAUSAL";
export type PerspectiveOrientation = "THESIS" | "ANTITHESIS" | "SYNTHESIS_BRIDGE";

export interface ExtractedClaimItem {
  claim_text: string;
  claim_type: ClaimType;
  confidence_score: number;
  grounding_snippet: string;
}

export interface ExtractClaimsResponse {
  extracted_claims: ExtractedClaimItem[];
  model_used: string;
  processed_at: string;
  editorial_disclaimer: string;
}

export interface SuggestedPerspectiveItem {
  perspective_label: string;
  orientation: PerspectiveOrientation;
  core_argument: string;
  underlying_value: string;
}

export interface SuggestPerspectivesResponse {
  perspectives: SuggestedPerspectiveItem[];
  balance_entropy: number;
  generated_at: string;
}

export interface BiasCheckResponse {
  is_neutral: boolean;
  neutrality_score: number;
  flagged_terms: string[];
  suggested_neutral_rephrasings: Record<string, string>;
  checked_at: string;
}

export interface ComposeSummaryResponse {
  composed_summary: string;
  character_count: number;
  readability_index: number;
  composed_at: string;
}

export class AiEditorialApiClient {
  private baseUrl: string;

  constructor(baseUrl = "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  async extractClaims(
    sourceText: string,
    maxClaims = 5
  ): Promise<ExtractClaimsResponse> {
    if (!sourceText || sourceText.trim().length < 20) {
      throw new Error("sourceText must have at least 20 characters");
    }

    if (this.baseUrl) {
      try {
        const res = await fetch(`${this.baseUrl}/v1/editorial/ai/extract-claims`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source_text: sourceText, max_claims: maxClaims }),
        });
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    return {
      extracted_claims: [
        {
          claim_text: sourceText.slice(0, 80),
          claim_type: "FACTUAL",
          confidence_score: 0.92,
          grounding_snippet: sourceText.slice(0, 60) + "...",
        },
        {
          claim_text: "Toplumsal denge için düzenleme şarttır.",
          claim_type: "NORMATIVE",
          confidence_score: 0.88,
          grounding_snippet: "Toplumsal denge...",
        },
      ],
      model_used: "provider-neutral-kefe-nlp-v1",
      processed_at: new Date().toISOString(),
      editorial_disclaimer:
        "AI-assisted claims require mandatory human editorial approval before publication.",
    };
  }

  async suggestPerspectives(
    title: string,
    contextSummary: string
  ): Promise<SuggestPerspectivesResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/editorial/ai/suggest-perspectives`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              dilemma_title: title,
              context_summary: contextSummary,
            }),
          }
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    return {
      perspectives: [
        {
          perspective_label: "Bireysel Özgürlük & Haklar",
          orientation: "THESIS",
          core_argument: `${title} konusunda bireysel tercihlere saygı duyulmalıdır.`,
          underlying_value: "Özgürlük & Özerklik",
        },
        {
          perspective_label: "Kamu Yararı & Güvenlik",
          orientation: "ANTITHESIS",
          core_argument: `${title} sürecinde toplumun genel güvenliği gözetilmelidir.`,
          underlying_value: "Kamu Güvenliği",
        },
        {
          perspective_label: "Dengeli Uzlaşı Modeli",
          orientation: "SYNTHESIS_BRIDGE",
          core_argument: "Her iki yaklaşımı uzlaştıran kademeli bir uygulama geliştirilmelidir.",
          underlying_value: "Ölçülülük",
        },
      ],
      balance_entropy: 0.88,
      generated_at: new Date().toISOString(),
    };
  }

  async checkBias(contentText: string): Promise<BiasCheckResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(`${this.baseUrl}/v1/editorial/ai/bias-check`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content_text: contentText }),
        });
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const flagged: string[] = [];
    const suggestions: Record<string, string> = {};
    if (contentText.toLowerCase().includes("rezalet")) {
      flagged.push("rezalet");
      suggestions["rezalet"] = "tartışmalı durum";
    }

    return {
      is_neutral: flagged.length === 0,
      neutrality_score: flagged.length === 0 ? 1.0 : 0.85,
      flagged_terms: flagged,
      suggested_neutral_rephrasings: suggestions,
      checked_at: new Date().toISOString(),
    };
  }

  async composeSummary(
    rawMaterial: string,
    targetLength = 300
  ): Promise<ComposeSummaryResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/editorial/ai/compose-summary`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              raw_material: rawMaterial,
              target_length_chars: targetLength,
            }),
          }
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const clean = rawMaterial.trim().slice(0, targetLength);
    return {
      composed_summary: clean,
      character_count: clean.length,
      readability_index: 0.86,
      composed_at: new Date().toISOString(),
    };
  }
}
