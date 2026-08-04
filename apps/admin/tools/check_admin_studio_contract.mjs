import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const repositoryRoot = resolve(root, "../..");

function read(relativePath) {
  return readFileSync(resolve(repositoryRoot, relativePath), "utf8");
}

function requireText(source, expected, context) {
  if (!source.includes(expected)) {
    throw new Error(`${context}: missing required text ${JSON.stringify(expected)}`);
  }
}

function forbidText(source, forbidden, context) {
  if (source.includes(forbidden)) {
    throw new Error(`${context}: forbidden text ${JSON.stringify(forbidden)}`);
  }
}

const contract = JSON.parse(
  read("docs/contracts/admin-studio-editorial-workspace.v1.json")
);
const packageJson = JSON.parse(read("apps/admin/package.json"));
const apiClient = read("apps/admin/src/lib/admin-api.ts");
const workspace = read("apps/admin/src/components/editorial-workspace.tsx");
const primitives = read("apps/admin/src/components/workspace-primitives.tsx");
const styles = read("apps/admin/app/globals.css");
const workflow = read(".github/workflows/admin-studio.yml");

if (contract.contract !== "admin-studio-editorial-workspace") {
  throw new Error("contract identity drift");
}
if (contract.version !== "1.0.0" || contract.status !== "accepted-for-implementation") {
  throw new Error("contract lifecycle/version drift");
}
if (contract.application.path !== "apps/admin") {
  throw new Error("Admin Studio application path drift");
}
if (contract.application.runtime_authority !== "canonical-api") {
  throw new Error("canonical API authority must remain explicit");
}
if (contract.application.parallel_domain_model_forbidden !== true) {
  throw new Error("parallel Admin domain model must remain forbidden");
}

for (const script of ["contract", "lint", "typecheck", "test", "build", "verify"]) {
  if (!packageJson.scripts?.[script]) {
    throw new Error(`package script missing: ${script}`);
  }
}

for (const required of [
  'credentials: "include"',
  'headers.set("X-KEFE-CSRF", this.csrfToken)',
  "WRITE_METHODS.has(upperMethod)",
  'redirect: "error"',
  'cache: "no-store"'
]) {
  requireText(apiClient, required, "Admin API security boundary");
}

for (const forbidden of [
  "localStorage",
  "sessionStorage",
  "dangerouslySetInnerHTML",
  "document.cookie",
  "eval(",
  "new Function("
]) {
  forbidText(apiClient, forbidden, "Admin API client");
  forbidText(workspace, forbidden, "Admin workspace");
}

for (const stage of ["QUEUE", "REVIEW", "BUNDLE", "PROJECTION"]) {
  requireText(primitives, stage, "workspace stage contract");
}
for (const explicitHandler of [
  "submitReview",
  "submitBundle",
  "submitProjection",
  "deriveProjectionKey"
]) {
  requireText(workspace, explicitHandler, "explicit operator action contract");
}
for (const forbiddenAutomaticSurface of [
  "useEffect(",
  "setInterval(",
  "setTimeout(",
  "/submit",
  "/approve",
  "/publish",
  "autoSubmit",
  "automaticReview",
  "automaticProjection"
]) {
  forbidText(workspace, forbiddenAutomaticSurface, "no automatic mutation/publication boundary");
}

requireText(workspace, 'type="submit"', "explicit form submission");
requireText(workspace, "Content Authoring", "DRAFT-only projection disclosure");
requireText(workspace, "Bu ekranda yayınlama yetkisi yoktur.", "publication exclusion disclosure");
requireText(styles, "prefers-reduced-motion", "reduced motion contract");
requireText(styles, "focus-visible", "keyboard focus contract");
requireText(styles, "prefers-color-scheme: light", "light theme contract");
requireText(primitives, 'aria-current={active === stage ? "step" : undefined}', "semantic stage contract");
requireText(workflow, "npm run verify", "dedicated verification workflow");
requireText(workflow, "apps/admin/**", "workflow path coverage");

if (contract.workspace.automatic_review_forbidden !== true) {
  throw new Error("automatic review must remain forbidden");
}
if (contract.workspace.automatic_bundle_forbidden !== true) {
  throw new Error("automatic bundle creation must remain forbidden");
}
if (contract.workspace.automatic_projection_forbidden !== true) {
  throw new Error("automatic projection must remain forbidden");
}
if (
  contract.workspace.authoring_submit_forbidden !== true ||
  contract.workspace.authoring_approve_forbidden !== true ||
  contract.workspace.authoring_publish_forbidden !== true
) {
  throw new Error("authoring lifecycle exclusion drift");
}
if (contract.security.csrf_required_for_methods.join(",") !== "POST,PUT,PATCH,DELETE") {
  throw new Error("write CSRF method boundary drift");
}

console.log("Admin Studio executable contract: PASS");
