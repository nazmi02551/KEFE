import Link from "next/link";

import styles from "@/app/home.module.css";
import { EditorialWorkspace } from "@/src/components/editorial-workspace";

export default function AdminStudioPage() {
  return (
    <>
      <nav aria-label="Admin Studio yüzeyleri" className={styles.navigation}>
        <Link href="/case-builder">Case Builder DRAFT çalışma alanını aç</Link>
        <Link href="/content-review">Editorial Quality Review alanını aç</Link>
        <Link href="/flow-composer">Flow Composer DRAFT alanını aç</Link>
        <Link href="/publication-operations">Publication Operations alanını aç</Link>
        <Link href="/reason-moderation">Community Reason Moderation alanını aç</Link>
        <Link href="/operational-reports">Operational Reports alanını aç</Link>
        <Link href="/case-media">Case Media Registry alanını aç</Link>
      </nav>
      <EditorialWorkspace />
    </>
  );
}
