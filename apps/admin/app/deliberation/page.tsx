import { DeliberationWorkspace } from "@/src/components/deliberation-workspace";

export const metadata = {
  title: "Deliberation & Kalite Denetimi — KEFE Admin Studio",
  description: "Vaka kalite kontrol kriterleri, halk itirazları ve şeffaf düzeltme geçmişi.",
};

export default async function DeliberationPage({
  searchParams,
}: {
  searchParams: Promise<{ version?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawVersion = Array.isArray(params.version) ? params.version[0] : params.version;
  const initialVersion = rawVersion || "22222222-2222-4222-8222-222222222222";
  const baseUrl = process.env.KEFE_API_BASE_URL ?? "http://localhost:8000";

  return (
    <main>
      <DeliberationWorkspace
        initialCaseVersionId={initialVersion}
        initialBaseUrl={baseUrl}
      />
    </main>
  );
}
