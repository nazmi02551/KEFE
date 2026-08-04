import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const repoRoot = path.resolve(appRoot, "../..");

const contract = JSON.parse(
  fs.readFileSync(
    path.join(repoRoot, "docs/contracts/admin-case-builder-draft-workspace.v1.json"),
    "utf8"
  )
);
const component = fs.readFileSync(
  path.join(appRoot, "src/components/case-builder-workspace.tsx"),
  "utf8"
);
const client = fs.readFileSync(
  path.join(appRoot, "src/lib/admin-api.ts"),
  "utf8"
);
const helpers = fs.readFileSync(
  path.join(appRoot, "src/lib/case-builder.ts"),
  "utf8"
);
const route = fs.readFileSync(
  path.join(appRoot, "app/case-builder/page.tsx"),
  "utf8"
);
const css = fs.readFileSync(
  path.join(appRoot, "src/components/case-builder-workspace.module.css"),
  "utf8"
);

const problems = [];

if (contract.version !== "1.0.1") {
  problems.push("Case Builder UI contract must consume contract version 1.0.1");
}
if (contract.workspace?.route !== "/case-builder") {
  problems.push("Case Builder route contract drifted");
}

const requiredComponent = [
  '"use client"',
  "caseBuilderVersion(normalized)",
  "saveCaseBuilderDraft(",
  "submitCaseVersion(version.id)",
  "caseAudit(version.case_id)",
  "Kaydedilmemiş değişiklikler var",
  "Yalnız DRAFT'ı kaydet",
  "Ayrı komutla incelemeye gönder",
  'aria-live="polite"',
  'role="status"',
  "flow_template_code",
  "completed_review_modes",
  "raw evidence",
  "setSubmitAcknowledged"
];
for (const fragment of requiredComponent) {
  if (!component.includes(fragment)) {
    problems.push(`Case Builder component missing: ${fragment}`);
  }
}

for (const forbidden of [
  "useEffect(",
  "localStorage",
  "sessionStorage",
  "dangerouslySetInnerHTML",
  "WebGL",
  "requestAnimationFrame",
  ".approveCase",
  ".publishCase",
  ".withdrawCase",
  ".rejectCase"
]) {
  if (component.includes(forbidden)) {
    problems.push(`Case Builder component contains forbidden behavior: ${forbidden}`);
  }
}

const requiredClient = [
  "/internal/admin/v1/case-builder/case-versions/",
  'return this.request(\n      "GET"',
  'return this.request(\n      "PUT"',
  "/internal/admin/v1/case-versions/",
  "/submit",
  "/audit"
];
for (const fragment of requiredClient) {
  if (!client.includes(fragment)) {
    problems.push(`Case Builder API client missing: ${fragment}`);
  }
}

for (const forbidden of [
  "flow_template_code: version.flow_template_code",
  "completed_review_modes: version.completed_review_modes",
  "published_at: version.published_at"
]) {
  if (helpers.includes(forbidden)) {
    problems.push(`Draft materialization leaks server-owned field: ${forbidden}`);
  }
}

if (!route.includes("initialVersionId={rawVersion ?? \"\"}")) {
  problems.push("Case Builder route must only prefill the query parameter");
}
if (route.includes("fetch(") || route.includes("caseBuilderVersion(")) {
  problems.push("Case Builder route must not fetch on mount");
}

for (const fragment of [
  ":focus-visible",
  "@media (max-width: 640px)",
  "@media (prefers-reduced-motion: reduce)",
  "data-state=\"DRAFT\""
]) {
  if (!css.includes(fragment)) {
    problems.push(`Case Builder accessibility CSS missing: ${fragment}`);
  }
}

if (problems.length > 0) {
  throw new Error(problems.join("\n"));
}

console.log(
  "Admin Case Builder UI contract: PASS — explicit load/save/audit/submit, " +
    "no request-on-mount, no browser credential persistence and no review/publication controls."
);
