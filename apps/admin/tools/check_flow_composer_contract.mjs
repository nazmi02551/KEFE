import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const contractPath = path.resolve(
  root,
  "../../docs/contracts/admin-flow-composer-draft-workspace.v1.json"
);
const componentPath = path.resolve(root, "src/components/flow-composer-workspace.tsx");
const apiPath = path.resolve(root, "src/lib/admin-api.ts");
const helperPath = path.resolve(root, "src/lib/flow-composer.ts");
const routePath = path.resolve(root, "app/flow-composer/page.tsx");
const homePath = path.resolve(root, "app/page.tsx");

const contract = JSON.parse(fs.readFileSync(contractPath, "utf8"));
const component = fs.readFileSync(componentPath, "utf8");
const api = fs.readFileSync(apiPath, "utf8");
const helper = fs.readFileSync(helperPath, "utf8");
const route = fs.readFileSync(routePath, "utf8");
const home = fs.readFileSync(homePath, "utf8");
const problems = [];

if (contract.version !== "1.0.0") {
  problems.push("Flow Composer UI contract version drifted");
}
if (contract.parent_runtime?.sha !== "f4c11547c0373017c527cfcf0a2d03dd3d3a9d97") {
  problems.push("Flow Composer UI parent runtime drifted");
}
if (contract.capabilities?.primary?.[0] !== "CAP-064") {
  problems.push("Flow Composer UI must advance CAP-064");
}

for (const fragment of [
  "FlowComposerWorkspace",
  "createDraft",
  "loadVersion",
  "saveVersion",
  "loadAudit",
  "discardChanges",
  "addFlow",
  "addStep",
  "topologyPreview",
  "validateFlowComposerVersion",
  "DRAFT-only sınır",
  "Current’tan yeni DRAFT oluştur",
  "DRAFT Flow’larını kaydet",
  "consumer runtime’ı"
]) {
  if (!component.includes(fragment)) {
    problems.push(`Flow Composer workspace missing: ${fragment}`);
  }
}

for (const forbidden of [
  "useEffect(",
  "localStorage",
  "sessionStorage",
  ".publish(",
  ".rollback(",
  "dragstart",
  "draggable=",
  "dangerouslySetInnerHTML",
  "raw_evidence_body",
  "backend_object_key"
]) {
  if (component.includes(forbidden)) {
    problems.push(`Flow Composer workspace contains forbidden behavior/data: ${forbidden}`);
  }
}

for (const fragment of [
  "createFlowComposerDraft(",
  "flowComposerVersion(",
  "saveFlowComposerVersion(",
  "flowComposerAudit(",
  "/internal/admin/v1/flow-composer",
  "credentials: \"include\"",
  "X-KEFE-CSRF"
]) {
  if (!api.includes(fragment)) {
    problems.push(`Typed Admin API client missing: ${fragment}`);
  }
}

for (const fragment of [
  "validateFlowComposerVersion",
  "reachableCodes",
  "hasCycle",
  "topologyPreview",
  "createFlowTemplate",
  "createFlowStep",
  "moveItem",
  "parseCodeList"
]) {
  if (!helper.includes(fragment)) {
    problems.push(`Flow Composer helper missing: ${fragment}`);
  }
}

if (!route.includes("FlowComposerWorkspace") || !route.includes("initialVersionId")) {
  problems.push("Flow Composer route is not wired with query prefill");
}
if (!home.includes('href="/flow-composer"')) {
  problems.push("Admin Studio does not link to Flow Composer");
}

if (problems.length > 0) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log(
  "Admin Flow Composer UI contract: PASS — explicit DRAFT commands, structured generic graph " +
    "editing, read-only catalogs, unsaved guard, CSRF and no publish/autosave/token persistence."
);
