import { CaseBuilderWorkspace } from "@/src/components/case-builder-workspace";

export default async function CaseBuilderPage({
  searchParams
}: {
  searchParams: Promise<{ version?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawVersion = Array.isArray(params.version) ? params.version[0] : params.version;
  return <CaseBuilderWorkspace initialVersionId={rawVersion ?? ""} />;
}
