import { SignalWorkspace } from "@/src/components/signal-workspace";

export const metadata = {
  title: "Sinyal Panosu — KEFE Admin Studio",
  description: "Metodoloji ile nitelendirilmiş sinyal sonuçlarını görüntüle.",
};

/**
 * Signal page — read-only signal dashboard.
 *
 * SignalWorkspace fetches in the browser, so only the explicitly public API
 * origin may be passed to it. Auth remains in the same-site Admin cookie.
 */
export default function SignalPage() {
  const baseUrl = process.env.NEXT_PUBLIC_KEFE_API_BASE_URL ?? "http://localhost:8000";

  return (
    <main>
      <SignalWorkspace baseUrl={baseUrl} />
    </main>
  );
}
