import { SignalWorkspace } from "@/src/components/signal-workspace";

export const metadata = {
  title: "Sinyal Panosu — KEFE Admin Studio",
  description: "Metodoloji ile nitelendirilmiş sinyal sonuçlarını görüntüle.",
};

/**
 * Signal page — read-only signal dashboard.
 *
 * KEFE_API_BASE_URL is set in .env.local and never exposed to the client.
 * The SignalWorkspace component fetches directly from the API base URL,
 * which in production should be a server-side Next.js route handler proxy
 * to avoid CORS and to attach server-side auth headers.
 */
export default function SignalPage() {
  const baseUrl = process.env.KEFE_API_BASE_URL ?? "http://localhost:8000";

  return (
    <main>
      <SignalWorkspace baseUrl={baseUrl} />
    </main>
  );
}