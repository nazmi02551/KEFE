import { EditorialQualityReviewWorkspace } from "@/src/components/editorial-quality-review-workspace";

export default async function EditorialQualityReviewPage({
  searchParams
}: {
  searchParams: Promise<{ version?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawVersion = Array.isArray(params.version) ? params.version[0] : params.version;
  return <EditorialQualityReviewWorkspace initialVersionId={rawVersion ?? ""} />;
}
