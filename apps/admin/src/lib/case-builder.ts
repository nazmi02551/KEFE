import type {
  CaseBuilderContextBlock,
  CaseBuilderDraftInput,
  CaseBuilderIssue,
  CaseBuilderLocalization,
  CaseBuilderSource,
  CaseBuilderVersion
} from "@/src/lib/contracts";

export type JsonSectionKey =
  | "issues"
  | "context_blocks"
  | "sources"
  | "localizations";

export function splitLines(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function prettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function parseArray<T>(value: string, label: string): T[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw new Error(`${label} geçerli JSON olmalıdır.`);
  }
  if (!Array.isArray(parsed)) {
    throw new Error(`${label} bir JSON dizisi olmalıdır.`);
  }
  return parsed as T[];
}

export function parseJsonSection(
  key: JsonSectionKey,
  value: string
):
  | CaseBuilderIssue[]
  | CaseBuilderContextBlock[]
  | CaseBuilderSource[]
  | CaseBuilderLocalization[] {
  switch (key) {
    case "issues":
      return parseArray<CaseBuilderIssue>(value, "Meseleler ve sorular");
    case "context_blocks":
      return parseArray<CaseBuilderContextBlock>(value, "Bağlam blokları");
    case "sources":
      return parseArray<CaseBuilderSource>(value, "Kaynaklar");
    case "localizations":
      return parseArray<CaseBuilderLocalization>(value, "Yerelleştirmeler");
  }
}

export function toDraftInput(version: CaseBuilderVersion): CaseBuilderDraftInput {
  return {
    title: version.title,
    summary: version.summary,
    base_format_code: version.base_format_code,
    primary_domain_code: version.primary_domain_code,
    content_risk: version.content_risk,
    issues: version.issues,
    context_blocks: version.context_blocks,
    sources: version.sources,
    modifiers: version.modifiers,
    is_fact_bearing: version.is_fact_bearing,
    is_real_event: version.is_real_event,
    required_review_modes: version.required_review_modes,
    content_locale: version.content_locale,
    market_scope: version.market_scope,
    country_codes: version.country_codes,
    cultural_context_note: version.cultural_context_note,
    legal_context_note: version.legal_context_note,
    localizations: version.localizations
  };
}

export function validateDraft(version: CaseBuilderVersion): string[] {
  const problems: string[] = [];
  if (version.state !== "DRAFT") problems.push("Yalnız DRAFT sürümü düzenlenebilir.");
  if (!version.title.trim()) problems.push("Başlık zorunludur.");
  if (!version.summary.trim()) problems.push("Özet zorunludur.");
  if (!version.base_format_code.trim()) problems.push("Temel format zorunludur.");
  if (!version.primary_domain_code.trim()) problems.push("Ana alan zorunludur.");
  if (!version.content_locale.trim()) problems.push("İçerik dili zorunludur.");
  if (version.issues.length === 0) problems.push("En az bir mesele gereklidir.");
  if (
    version.market_scope === "COUNTRY_SET" &&
    version.country_codes.length === 0
  ) {
    problems.push("COUNTRY_SET için en az bir ülke kodu gereklidir.");
  }
  return problems;
}
