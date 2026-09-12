import { ClaimWorkspace } from "@/src/components/claim-workspace";

export const metadata = {
  title: "İddia & Bilgi Grafiği — KEFE Admin Studio",
  description: "Birinci sınıf iddia sınıflandırması, kanıt değerlendirme döngüsü ve iddia-argüman ağ ilişkileri.",
};

export default function ClaimsPage() {
  const baseUrl = process.env.KEFE_API_BASE_URL ?? "http://localhost:8000";

  return (
    <main>
      <ClaimWorkspace initialBaseUrl={baseUrl} />
    </main>
  );
}
