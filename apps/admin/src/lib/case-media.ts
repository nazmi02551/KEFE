export type MediaKind = "IMAGE" | "VIDEO";
export type MediaState = "REGISTERED" | "READY" | "RETIRED";
export type MediaSlot = "HERO" | "CONTEXT" | "REVEAL" | "IMPACT";

export interface MediaAsset {
  media_asset_id: string;
  asset_key: string;
  kind: MediaKind;
  delivery_ref: string;
  content_hash: string;
  byte_length: number;
  media_type: string;
  title: string;
  alt_text: string;
  caption: string | null;
  credit_label: string;
  source_label: string;
  poster_asset_key: string | null;
  state: MediaState;
  registered_by: string;
  registered_at: string;
}

export interface MediaInventory {
  items: MediaAsset[];
}

export interface MediaAssetWriteResponse {
  asset: MediaAsset;
  replayed: boolean;
}

export interface MediaAuditEntry {
  audit_id: string;
  media_asset_id: string;
  actor_ref: string;
  command: "REGISTER" | "MARK_READY" | "RETIRE";
  previous_state: MediaState | null;
  new_state: MediaState;
  occurred_at: string;
}

export interface MediaAuditTrail {
  items: MediaAuditEntry[];
}

export interface MediaBindingWriteResponse {
  binding: {
    binding_id: string;
    case_version_id: string;
    media_asset_id: string;
    slot: MediaSlot;
    priority: number;
    autoplay: boolean;
    muted: boolean;
    looping: boolean;
    bound_by: string;
    bound_at: string;
  };
  replayed: boolean;
}

export interface RegisterMediaRequest {
  asset_key: string;
  kind: MediaKind;
  delivery_ref: string;
  content_hash: string;
  byte_length: number;
  media_type: string;
  title: string;
  alt_text: string;
  caption: string | null;
  credit_label: string;
  source_label: string;
  poster_asset_key: string | null;
}

export interface BindMediaRequest {
  case_version_id: string;
  slot: MediaSlot;
  priority: number;
  autoplay: false;
  muted: boolean;
  looping: boolean;
}

export function boundedMediaText(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim()
    ? value.trim().slice(0, 500)
    : fallback;
}
