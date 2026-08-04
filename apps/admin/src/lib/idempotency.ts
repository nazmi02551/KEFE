const UUIDISH = /^[0-9a-f-]{8,64}$/i;

function normalizedIdentity(value: string, field: string): string {
  const normalized = value.trim().toLowerCase();
  if (!UUIDISH.test(normalized)) {
    throw new Error(`${field} must be a bounded canonical identity`);
  }
  return normalized;
}

export function projectionIdempotencyKey(
  candidateProposalId: string,
  reviewDecisionId: string
): string {
  const candidate = normalizedIdentity(candidateProposalId, "candidateProposalId");
  const review = normalizedIdentity(reviewDecisionId, "reviewDecisionId");
  return `admin-studio:projection:v1:${candidate}:${review}`;
}
