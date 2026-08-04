import { PublicationOperationsWorkspace } from "@/src/components/publication-operations-workspace";

export default async function PublicationOperationsPage({
  searchParams
}: {
  searchParams: Promise<{ version?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawVersion = Array.isArray(params.version) ? params.version[0] : params.version;
  return <PublicationOperationsWorkspace initialVersionId={rawVersion ?? ""} />;
}
