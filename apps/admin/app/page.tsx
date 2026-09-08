import Link from "next/link";

import styles from "@/app/home.module.css";
import { EditorialWorkspace } from "@/src/components/editorial-workspace";
import { ThemeToggle } from "@/src/components/theme-toggle";

export default function AdminStudioPage() {
  return (
    <>
      <nav aria-label="Admin Studio yüzeyleri" className={styles.navigation}>
        <div className={styles.navLinks}>
          <Link href="/case-builder">Case Builder DRAFT</Link>
          <Link href="/content-review">Editorial Quality Review</Link>
          <Link href="/flow-composer">Flow Composer DRAFT</Link>
          <Link href="/publication-operations">Publication Operations</Link>
          <Link href="/reason-moderation">Community Reason Moderation</Link>
          <Link href="/operational-reports">Operational Reports</Link>
          <Link href="/case-media">Case Media Registry</Link>
        </div>
        <ThemeToggle />
      </nav>
      <EditorialWorkspace />
    </>
  );
}
