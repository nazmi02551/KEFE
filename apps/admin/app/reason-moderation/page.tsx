import { ReasonModerationWorkspace } from "@/src/components/reason-moderation-workspace";

export default async function ReasonModerationPage({
  searchParams
}: {
  searchParams: Promise<{ reason?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawReason = Array.isArray(params.reason) ? params.reason[0] : params.reason;
  return <ReasonModerationWorkspace initialReasonId={rawReason ?? ""} />;
}
