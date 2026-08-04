import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const contractPath = path.resolve(
  root,
  "../../docs/contracts/admin-publication-operations-workspace.v1.json"
);
const componentPath = path.resolve(
  root,
  "src/components/publication-operations-workspace.tsx"
);
const helperPath = path.resolve(root, "src/lib/publication-operations.ts");
const apiPath = path.resolve(root, "src/lib/admin-api.ts");
const routePath = path.resolve(root, "app/publication-operations/page.tsx");
const homePath = path.resolve(root, "app/page.tsx");

const contract = JSON.parse(fs.readFileSync(contractPath, "utf8"));
const component = fs.readFileSync(componentPath, "utf8");
const helper = fs.readFileSync(helperPath, "utf8");
const api = fs.readFileSync(apiPath, "utf8");
const route = fs.readFileSync(routePath, "utf8");
const home = fs.readFileSync(homePath, "utf8");
const problems = [];

if (contract.contract_id !== "admin-publication-operations-workspace.v1") {
  problems.push("Publication Operations contract identity drifted");
}
if (contract.version !== "1.0.0") {
  problems.push("Publication Operations UI contract version drifted");
}
if (contract.parent_runtime?.sha !== "62dd27dfa2000d818cecf16af9627c54f98a245a") {
  problems.push("Publication Operations parent runtime drifted");
}
if (contract.capabilities?.primary?.join(",") !== "CAP-065") {
  problems.push("Publication Operations primary capability drifted");
}
if (contract.capabilities?.lifecycle_promotion !== false) {
  problems.push("Publication Operations cannot promote capability lifecycle");
}

for (const fragment of [
  "PublicationOperationsWorkspace",
  "loadQueue",
  "loadDetail",
  "runPreflight",
  "loadAudit",
  "publishConfirmed",
  "withdrawRationale",
  "Advisory preflight çalıştır",
  "Yayımla · güncel doğrulamayı tekrar çalıştır",
  "Gerekçeyle yayından çek",
  "İstekler otomatik başlamaz"
]) {
  if (!component.includes(fragment)) {
    problems.push(`Publication Operations workspace missing: ${fragment}`);
  }
}

for (const forbidden of [
  "useEffect(",
  "localStorage",
  "sessionStorage",
  "dangerouslySetInnerHTML",
  ".approve(",
  ".reject(",
  "saveCaseBuilderDraft",
  "saveFlowComposerVersion",
  "createFlowComposerDraft",
  "publishConfiguration",
  "rollback"
]) {
  if (component.includes(forbidden)) {
    problems.push(`Publication Operations contains forbidden behavior: ${forbidden}`);
  }
}

for (const fragment of [
  "canPublish",
  "canWithdraw",
  "publishRequest",
  "withdrawRequest",
  "preflightFingerprint"
]) {
  if (!helper.includes(fragment)) {
    problems.push(`Publication Operations helper missing: ${fragment}`);
  }
}

for (const fragment of [
  "publicationOperations(",
  "publicationOperation(",
  "publicationPreflight(",
  "decidePublication(",
  "/internal/admin/v1/publication-operations",
  "credentials: \"include\"",
  "X-KEFE-CSRF"
]) {
  if (!api.includes(fragment)) {
    problems.push(`Typed Admin API client missing: ${fragment}`);
  }
}

if (!route.includes("PublicationOperationsWorkspace")) {
  problems.push("Publication Operations route is not wired to the workspace");
}
if (!home.includes('href="/publication-operations"')) {
  problems.push("Admin Studio does not link Publication Operations");
}

if (problems.length > 0) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log(
  "Admin Publication Operations UI contract: PASS — explicit bounded queues, " +
    "read-only detail, advisory preflight, confirmed publish, reasoned withdraw, " +
    "same-session CSRF and no automatic/edit/review/configuration shortcuts."
);
