import React from "react";

import type { ProposalReviewState } from "@/src/lib/contracts";

export type WorkspaceStage = "QUEUE" | "REVIEW" | "BUNDLE" | "PROJECTION";

const STAGE_LABELS: Record<WorkspaceStage, string> = {
  QUEUE: "İş listesi",
  REVIEW: "İnceleme",
  BUNDLE: "Aday paket",
  PROJECTION: "Taslağa aktarım"
};

export function StatusBadge({ state }: { state: ProposalReviewState | string }) {
  return (
    <span className="statusBadge" data-state={state} aria-label={`Durum: ${state}`}>
      {state}
    </span>
  );
}

export function WorkspaceStepper({
  active,
  onSelect
}: {
  active: WorkspaceStage;
  onSelect?: (stage: WorkspaceStage) => void;
}) {
  const stages = Object.keys(STAGE_LABELS) as WorkspaceStage[];
  return (
    <nav aria-label="Editoryal çalışma aşamaları" className="workspaceStepper">
      {stages.map((stage, index) => (
        <button
          className="stepButton"
          aria-current={active === stage ? "step" : undefined}
          key={stage}
          onClick={() => onSelect?.(stage)}
          type="button"
        >
          <span aria-hidden="true" className="stepIndex">
            {index + 1}
          </span>
          <span>{STAGE_LABELS[stage]}</span>
        </button>
      ))}
    </nav>
  );
}
