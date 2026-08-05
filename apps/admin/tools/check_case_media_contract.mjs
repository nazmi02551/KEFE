import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const contract = JSON.parse(
  fs.readFileSync(
    path.resolve(
      root,
      "../../docs/contracts/admin-case-media-asset-management.v1.json"
    ),
    "utf8"
  )
);
const component = fs.readFileSync(
  path.resolve(root, "src/components/case-media-workspace.tsx"),
  "utf8"
);
const api = fs.readFileSync(
  path.resolve(root, "src/lib/case-media-api.ts"),
  "utf8"
);
const types = fs.readFileSync(
  path.resolve(root, "src/lib/case-media.ts"),
  "utf8"
);
const route = fs.readFileSync(
  path.resolve(root, "app/case-media/page.tsx"),
  "utf8"
);
const home = fs.readFileSync(path.resolve(root, "app/page.tsx"), "utf8");
const problems = [];

if (contract.contract_version !== "1.0.0") {
  problems.push("Case Media contract version drifted");
}
if (contract.parent?.exact_head !== "d2644bbcc2c7eb970c507f72e610ae35000c3798") {
  problems.push("Case Media exact parent drifted");
}
if (contract.capabilities?.join(",") !== "CAP-094,CAP-126") {
  problems.push("Case Media capability scope drifted");
}
if (contract.production_projection?.preview_fallback_forbidden !== true) {
  problems.push("Preview fallback prohibition is not locked");
}
if (contract.admin_ui?.no_request_on_mount !== true) {
  problems.push("Request-on-mount must remain disabled");
}
if (contract.admin_ui?.no_binary_file_input !== true) {
  problems.push("Binary file input prohibition is not locked");
}
if (contract.admin_ui?.no_upload !== true) {
  problems.push("Upload prohibition is not locked");
}
if (contract.admin_security?.write_capability !== "MEDIA_ASSET_MANAGE") {
  problems.push("Dedicated media write capability is not locked");
}

for (const fragment of [
  "CaseMediaWorkspace",
  "verifySession",
  "loadInventory",
  "loadDetail",
  "loadAudit",
  "register",
  "markReady",
  "bind",
  "retire",
  "Register immutable metadata",
  "Fail-closed production boundary",
  "Autoplay is always false"
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
  'type="file"',
  "FormData(",
  "multipart",
  "signedUrl",
  "uploadFile",
  "autoPublish",
  "autoBind"
]) {
  if (component.includes(forbidden)) {
    problems.push(`Workspace contains forbidden behavior: ${forbidden}`);
  }
}

for (const fragment of [
  "CaseMediaApiClient",
  "/internal/admin/v1/case-media",
  'credentials: "include"',
  'cache: "no-store"',
  "ADMIN_API_BASE_INSECURE",
  "ADMIN_CSRF_REQUIRED",
  'headers.set("X-KEFE-CSRF"',
  "inventory(",
  "detail(",
  "audit(",
  "register(",
  "markReady(",
  "bind(",
  "retire("
]) {
  if (!api.includes(fragment)) {
    problems.push(`API client missing: ${fragment}`);
  }
}
for (const forbidden of [
  "localStorage",
  "sessionStorage",
  "setInterval(",
  "FormData(",
  "multipart",
  "UploadFile"
]) {
  if (api.includes(forbidden)) {
    problems.push(`API client contains forbidden behavior: ${forbidden}`);
  }
}

for (const fragment of [
  'export type MediaKind = "IMAGE" | "VIDEO"',
  'export type MediaState = "REGISTERED" | "READY" | "RETIRED"',
  'export type MediaSlot = "HERO" | "CONTEXT" | "REVEAL" | "IMPACT"',
  "autoplay: false"
]) {
  if (!types.includes(fragment)) {
    problems.push(`Typed contract missing: ${fragment}`);
  }
}

if (!route.includes("CaseMediaWorkspace")) {
  problems.push("Case Media route is not wired");
}
if (!home.includes('href="/case-media"')) {
  problems.push("Admin Studio does not link Case Media");
}

for (const temporaryPath of [
  "tools/_case_media_checker.template",
  "../../services/api/tools/_case_media_checker.template",
  "../../services/api/tools/_case_media_openapi.template"
]) {
  if (fs.existsSync(path.resolve(root, temporaryPath))) {
    problems.push(`Temporary Case Media template remains: ${temporaryPath}`);
  }
}

if (problems.length) {
  console.error(problems.join("\n"));
  process.exit(1);
}

console.log(
  "Admin Case Media UI contract: PASS — explicit metadata commands, same-session CSRF, " +
    "no request on mount, no polling/browser storage/binary upload, and no Preview fallback."
);
