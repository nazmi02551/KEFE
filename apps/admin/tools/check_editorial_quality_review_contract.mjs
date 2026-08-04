import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const contractPath = path.resolve(
  root,
  "../../docs/contracts/admin-editorial-quality-review-workspace.v1.json"
);
const componentPath = path.resolve(
  root,
  "src/components/editorial-quality-review-workspace.tsx"
);
const apiPath = path.resolve(root, "src/lib/admin-api.ts");
const helperPath = path.resolve(root, "src/lib/editorial-quality-review.ts");
const routePath = path.resolve(root, "app/content-review/page.tsx");

const contract = JSON.parse(fs.readFileSync(contractPath, "utf8"));
const component = fs.readFileSync(componentPath, "utf8");
const api = fs.readFileSync(apiPath, "utf8");
const helper = fs.readFileSync(helperPath, "utf8");
const route = fs.readFileSync(routePath, "utf8");
const problems = [];

if (contract.version !== "1.0.0") {
  problems.push("Editorial Quality Review UI contract version drifted");
}
if (contract.parent_runtime?.sha !== "612c57fa2188c7f9c5fae8f64fcfebbca644cfbc") {
  problems.push("Editorial Quality Review UI parent runtime drifted");
}

for (const fragment of [
  "EditorialQualityReviewWorkspace",
  "loadQueue",
  "loadDetail",
  "loadAudit",
  "decideContentReview",
  "approveConfirmed",
  "completedModes",
  "rejectRationale",
  "Hiçbir istek otomatik başlatılmaz",
  "Onayla · yayınlama yok",
  "Gerekçeyle DRAFT’a döndür"
]) {
  if (!component.includes(fragment)) {
    problems.push(`Editorial review workspace missing: ${fragment}`);
  }
}

for (const forbidden of [
  "useEffect(",
  "localStorage",
  "sessionStorage",
  ".publish(",
  ".withdraw(",
  "raw_evidence_body",
  "provider_secret_ref",
  "backend_object_key",
  "dangerouslySetInnerHTML"
]) {
  if (component.includes(forbidden)) {
    problems.push(`Editorial review workspace contains forbidden behavior/data: ${forbidden}`);
  }
}

for (const fragment of [
  "contentReviews(",
  "contentReview(",
  "decideContentReview(",
  "/internal/admin/v1/content-reviews",
  "credentials: \"include\"",
  "X-KEFE-CSRF"
]) {
  if (!api.includes(fragment)) {
    problems.push(`Typed Admin API client missing: ${fragment}`);
  }
}

for (const fragment of [
  "reviewModesExactlyComplete",
  "canApproveEditorialReview",
  "canRejectEditorialReview",
  "approvalRequest",
  "rejectionRequest"
]) {
  if (!helper.includes(fragment)) {
    problems.push(`Editorial review helper missing: ${fragment}`);
  }
}

if (!route.includes("EditorialQualityReviewWorkspace")) {
  problems.push("Editorial quality review route is not wired to the workspace");
}

if (problems.length > 0) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log(
  "Admin Editorial Quality Review UI contract: PASS — explicit load, read-only inspection, " +
    "exact review-mode attestation, reasoned rejection, CSRF and no publish/autosave/persistence."
);
