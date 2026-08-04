import { FlowComposerWorkspace } from "@/src/components/flow-composer-workspace";

export default async function FlowComposerPage({
  searchParams
}: {
  searchParams: Promise<{ version?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawVersion = Array.isArray(params.version) ? params.version[0] : params.version;
  return <FlowComposerWorkspace initialVersionId={rawVersion ?? ""} />;
}
