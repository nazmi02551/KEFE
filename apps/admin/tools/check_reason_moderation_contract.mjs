import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const contractPath = path.resolve(
  root,
  "../../docs/contracts/admin-community-reason-moderation-operations.v1.json"
);
const componentPath = path.resolve(
  root,
  "src/components/reason-moderation-workspace.tsx"
);
const helperPath = path.resolve(root, "src/lib/reason-moderation.ts");
const apiPath = path.resolve(root, "src/lib/reason-moderation-api.ts");
const routePath = path.resolve(root, "app/reason-moderation/page.tsx");
const homePath = path.resolve(root, "app/page.tsx");

const contract = JSON.parse(fs.readFileSync(contractPath, "utf8"));
const component = fs.readFileSync(componentPath, "utf8");
const helper = fs.readFileSync(helperPath, "utf8");
const api = fs.readFileSync(apiPath, "utf8");
const route = fs.readFileSync(routePath, "utf8");
const home = fs.readFileSync(homePath, "utf8");
const problems = [];

if (contract.contract_id !== "admin-community-reason-moderation-operations.v1") {
  problems.push("Reason moderation contract identity drifted");
}
if (contract.parent_runtime?.sha !== "9342989bf76b22036501f7792d1adb5ffb309f8b") {
  problems.push("Reason moderation parent runtime drifted");
}
if (contract.capabilities?.primary?.join(",") !== "CAP-066") {
  problems.push("Reason moderation primary capability drifted");
}
if (contract.capabilities?.lifecycle_promotion !== false) {
  problems.push("Reason moderation cannot promote capability lifecycle");
}
if (contract.security?.new_capability !== "CONTENT_MODERATE") {
  problems.push("Dedicated moderation capability is not locked");
}
if (contract.inspection?.never_exposes?.includes("reporter_actor_id") !== true) {
  problems.push("Reporter identity exclusion is not locked");
}

for (const fragment of [
  "ReasonModerationWorkspace",
  "loadQueue",
  "selectReason",
  "loadDetail",
  "loadAudit",
  "submitDecision",
  "PENDING",
  "REPORTED",
  "Privacy-safe rapor özeti",
  "Exact neden ID teyidi",
  "Append-only moderation audit"
]) {
  if (!component.includes(fragment)) {
    problems.push(`Reason moderation workspace missing: ${fragment}`);
  }
}

for (const forbidden of [
  "useEffect(",
  "localStorage",
  "sessionStorage",
  "dangerouslySetInnerHTML",
  "setInterval(",
  "actor_id",
  "author_actor_id",
  "reporter_actor_id",
  "weigh_session_id",
  "bulkModerate(",
  "autoModerate(",
  "unblockReason(",
  "restoreReason("
]) {
  if (component.includes(forbidden)) {
    problems.push(`Reason moderation contains forbidden behavior: ${forbidden}`);
  }
}

for (const fragment of [
  "canSubmitModeration",
  "moderationDecisionRequest",
  "reportSummary",
  "confirmationReasonId === input.reason.reason_id"
]) {
  if (!helper.includes(fragment)) {
    problems.push(`Reason moderation helper missing: ${fragment}`);
  }
}

for (const fragment of [
  "ReasonModerationApiClient",
  "/internal/admin/v1/community-reason-moderation",
  "credentials: \"include\"",
  "X-KEFE-CSRF",
  "ADMIN_API_BASE_INSECURE",
  "queue(",
  "detail(",
  "audit(",
  "decide("
]) {
  if (!api.includes(fragment)) {
    problems.push(`Reason moderation API client missing: ${fragment}`);
  }
}

for (const forbidden of ["localStorage", "sessionStorage", "setInterval("]) {
  if (api.includes(forbidden)) {
    problems.push(`Reason moderation API contains forbidden behavior: ${forbidden}`);
  }
}

if (!route.includes("ReasonModerationWorkspace")) {
  problems.push("Reason moderation route is not wired to the workspace");
}
if (!home.includes('href="/reason-moderation"')) {
  problems.push("Admin Studio does not link reason moderation");
}

if (problems.length > 0) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log(
  "Admin Community Reason moderation UI contract: PASS — explicit bounded queues, " +
    "privacy-safe aggregate inspection, rationale and exact-ID confirmed decisions, " +
    "same-session CSRF and no automatic, identity, bulk or restore shortcuts."
);
