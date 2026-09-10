import { cookies } from "next/headers";
import { ImpactWorkspace } from "@/src/components/impact-workspace";

export const metadata = {
  title: "Etki Takip — KEFE Admin Studio",
  description: "Kurum yanıtları ve eylem kilometre taşlarını izle.",
};

/**
 * Impact page — institution responses + action milestone dashboard.
 *
 * csrfToken is read from the server-side session cookie to be forwarded
 * to mutation requests. In production this should be a signed CSRF token
 * from the Admin session store.
 */
export default async function ImpactPage({
  searchParams,
}: {
  searchParams: Promise<{ case_version_id?: string }>;
}) {
  const params = await searchParams;
  const baseUrl = process.env.KEFE_API_BASE_URL ?? "http://localhost:8000";

  // Read CSRF token from admin session cookie (set by /v1/admin/session/start).
  const cookieStore = await cookies();
  const csrfToken = cookieStore.get("kefe_admin_csrf")?.value ?? "";

  return (
    <main>
      <ImpactWorkspace
        baseUrl={baseUrl}
        csrfToken={csrfToken}
        caseVersionId={params.case_version_id}
      />
    </main>
  );
}