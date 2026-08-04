import type {
  EditorialReviewDecisionRequest,
  EditorialReviewDetail
} from "@/src/lib/contracts";

export function normalizeReviewModes(values: readonly string[]): string[] {
  return values.map((value) => value.trim()).filter(Boolean);
}

export function reviewModesExactlyComplete(
  required: readonly string[],
  completed: readonly string[]
): boolean {
  const normalizedRequired = normalizeReviewModes(required);
  const normalizedCompleted = normalizeReviewModes(completed);
  if (
    new Set(normalizedRequired).size !== normalizedRequired.length ||
    new Set(normalizedCompleted).size !== normalizedCompleted.length
  ) {
    return false;
  }
  if (normalizedRequired.length !== normalizedCompleted.length) return false;
  const completedSet = new Set(normalizedCompleted);
  return normalizedRequired.every((mode) => completedSet.has(mode));
}

export function canApproveEditorialReview(input: {
  detail: EditorialReviewDetail | null;
  completedReviewModes: readonly string[];
  confirmed: boolean;
  csrfToken: string;
}): boolean {
  return Boolean(
    input.detail?.version.state === "IN_REVIEW" &&
      input.confirmed &&
      input.csrfToken.trim() &&
      reviewModesExactlyComplete(
        input.detail.version.required_review_modes,
        input.completedReviewModes
      )
  );
}

export function canRejectEditorialReview(input: {
  detail: EditorialReviewDetail | null;
  rationale: string;
  csrfToken: string;
}): boolean {
  return Boolean(
    input.detail?.version.state === "IN_REVIEW" &&
      input.rationale.trim() &&
      input.csrfToken.trim()
  );
}

export function approvalRequest(
  completedReviewModes: readonly string[]
): EditorialReviewDecisionRequest {
  return {
    decision: "APPROVE",
    completed_review_modes: normalizeReviewModes(completedReviewModes)
  };
}

export function rejectionRequest(rationale: string): EditorialReviewDecisionRequest {
  return {
    decision: "REJECT",
    completed_review_modes: [],
    rationale: rationale.trim()
  };
}
