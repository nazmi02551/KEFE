import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const contract = JSON.parse(
  fs.readFileSync(
    path.resolve(
      root,
      "../../docs/contracts/admin-operational-reports-snapshot.v1.json"
    ),
    "utf8"
  )
);
const component = fs.readFileSync(
  path.resolve(root, "src/components/operational-reports-workspace.tsx"),
  "utf8"
);
const helper = fs.readFileSync(
  path.resolve(root, "src/lib/operational-reports.ts"),
  "utf8"
);
const api = fs.readFileSync(
  path.resolve(root, "src/lib/operational-reports-api.ts"),
  "utf8"
);
const route = fs.readFileSync(
  path.resolve(root, "app/operational-reports/page.tsx"),
  "utf8"
);
const home = fs.readFileSync(path.resolve(root, "app/page.tsx"), "utf8");
const problems = [];

if (contract.contract_id !== "admin-operational-reports-snapshot.v1") {
  problems.push("Operational Reports contract identity drifted");
}
if (
  contract.parent_runtime?.sha !==
  "6d5bc52388b590706a3a07aef9b2be08bc501aae"
) {
  problems.push("Operational Reports parent runtime drifted");
}
if (contract.capabilities?.primary?.join(",") !== "CAP-123") {
  problems.push("Operational Reports primary capability drifted");
}
if (contract.capabilities?.lifecycle_promotion !== false) {
  problems.push("Operational Reports cannot promote capability lifecycle");
}
if (contract.security?.new_capability !== "OPERATIONAL_REPORT_READ") {
  problems.push("Dedicated operational report capability is not locked");
}
if (contract.privacy?.aggregate_only !== true) {
  problems.push("Aggregate-only privacy boundary is not locked");
}
if (contract.admin_ui?.request_on_mount !== false) {
  problems.push("Request-on-mount must remain disabled");
}
if (contract.admin_ui?.polling !== false) {
  problems.push("Polling must remain disabled");
}
if (contract.admin_ui?.mutation !== false) {
  problems.push("Operational Reports must remain read-only");
}

for (const fragment of [
  "OperationalReportsWorkspace",
  "verifySession",
  "loadSnapshot",
  "Admin Operational Reports",
  "Şeffaf reason codes",
  "Görünür eşikler",
  "Aggregate-only privacy boundary",
  "Snapshot yükle"
]) {
  if (!component.includes(fragment)) {
    problems.push(`Workspace missing: ${fragment}`);
  }
}

for (const forbidden of [
  "useEffect(",
  "setInterval(",
  "localStorage",
  "sessionStorage",
  "dangerouslySetInnerHTML",
  "X-KEFE-CSRF",
  "autoRefresh",
  "exportReport(",
  "acknowledgeReport(",
  "remediate("
]) {
  if (component.includes(forbidden)) {
    problems.push(`Workspace contains forbidden behavior: ${forbidden}`);
  }
}

for (const fragment of [
  "operationalSignalText",
  "operationalReasonText",
  "sortedCountEntries",
  "totalOperationalCount"
]) {
  if (!helper.includes(fragment)) {
    problems.push(`Helper missing: ${fragment}`);
  }
}

for (const fragment of [
  "OperationalReportsApiClient",
  "/internal/admin/v1/operational-reports/snapshot",
  'method: "GET"',
  'credentials: "include"',
  'cache: "no-store"',
  "ADMIN_API_BASE_INSECURE",
  "session()",
  "snapshot()"
]) {
  if (!api.includes(fragment)) {
    problems.push(`API client missing: ${fragment}`);
  }
}
for (const forbidden of [
  "X-KEFE-CSRF",
  'method: "POST"',
  'method: "PUT"',
  'method: "PATCH"',
  'method: "DELETE"',
  "localStorage",
  "setInterval("
]) {
  if (api.includes(forbidden)) {
    problems.push(`API client contains forbidden behavior: ${forbidden}`);
  }
}

if (!route.includes("OperationalReportsWorkspace")) {
  problems.push("Operational Reports route is not wired");
}
if (!home.includes('href="/operational-reports"')) {
  problems.push("Admin Studio does not link Operational Reports");
}

const temporaryPaths = [
  "tools/_operational_reports_checker.template",
  "../../services/api/tools/_admin_operational_reports_checker.template",
  "../../services/api/tools/_admin_operational_reports_openapi.template"
];
for (const temporaryPath of temporaryPaths) {
  if (fs.existsSync(path.resolve(root, temporaryPath))) {
    problems.push(`Temporary Operational Reports template remains: ${temporaryPath}`);
  }
}

if (problems.length) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log(
  "Admin Operational Reports UI contract: PASS — explicit GET-only snapshot, " +
    "visible thresholds/reason codes, aggregate-only privacy and no polling, " +
    "browser storage or mutation."
);
