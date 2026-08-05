export type OperationalSignal = "QUIET" | "NOMINAL" | "ATTENTION" | "CRITICAL";

export interface OperationalThresholds {
  in_review_attention_threshold: number;
  pending_proposal_attention_threshold: number;
  moderation_candidate_attention_threshold: number;
}

export interface ContentSupplyPolicy {
  pending_dispatch_attention_threshold: number;
  queued_run_attention_threshold: number;
  unreviewed_proposal_attention_threshold: number;
  recent_non_success_attention_threshold: number;
  max_cycle_silence_seconds: number;
  failure_window_seconds: number;
}

export interface ContentSupplySnapshot {
  signal: OperationalSignal;
  as_of: string;
  reason_codes: string[];
  active_schedule_count: number;
  paused_schedule_count: number;
  due_schedule_count: number;
  pending_dispatch_count: number;
  running_dispatch_count: number;
  stale_dispatch_count: number;
  recent_dispatch_non_success_count: number;
  queued_ingestion_run_count: number;
  running_ingestion_run_count: number;
  stale_ingestion_lease_count: number;
  recent_failed_ingestion_run_count: number;
  unreviewed_proposal_count: number;
  running_cycle_count: number;
  stale_cycle_count: number;
  recent_non_success_cycle_count: number;
  latest_terminal_cycle_state: string | null;
  latest_terminal_cycle_completed_at: string | null;
  seconds_since_latest_terminal_cycle: number | null;
}

export interface OperationalReportsSnapshot {
  as_of: string;
  overall_signal: OperationalSignal;
  reason_codes: string[];
  thresholds: OperationalThresholds;
  content_supply_policy: ContentSupplyPolicy;
  content_supply: ContentSupplySnapshot;
  editorial_lifecycle: Record<string, number>;
  proposal_review: Record<string, number>;
  moderation: Record<string, number>;
  aggregate_only: true;
}

const SIGNAL_TEXT: Record<OperationalSignal, string> = {
  QUIET: "Sessiz",
  NOMINAL: "Normal",
  ATTENTION: "Dikkat",
  CRITICAL: "Kritik"
};

const REASON_TEXT: Record<string, string> = {
  CONTENT_SUPPLY_ATTENTION: "İçerik tedarik hattı dikkat gerektiriyor",
  CONTENT_SUPPLY_CRITICAL: "İçerik tedarik hattı kritik durumda",
  EDITORIAL_IN_REVIEW_BACKLOG: "İncelemedeki CaseVersion kuyruğu eşiği aştı",
  PROPOSAL_REVIEW_BACKLOG: "Bekleyen Proposal kuyruğu eşiği aştı",
  MODERATION_BACKLOG: "Aktif moderasyon kuyruğu eşiği aştı"
};

export function operationalSignalText(signal: OperationalSignal): string {
  return SIGNAL_TEXT[signal];
}

export function operationalReasonText(code: string): string {
  return REASON_TEXT[code] ?? code;
}

export function sortedCountEntries(
  values: Record<string, number>
): Array<[string, number]> {
  return Object.entries(values).sort(([left], [right]) => left.localeCompare(right));
}

export function totalOperationalCount(values: Record<string, number>): number {
  return Object.values(values).reduce((total, value) => total + value, 0);
}

export function boundedOperationalText(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback;
  const trimmed = value.trim();
  return trimmed ? trimmed.slice(0, 1000) : fallback;
}
