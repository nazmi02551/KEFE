#!/usr/bin/env node
/**
 * KEFE Web — Test runner
 *
 * Runs static structural and contract checks for apps/web.
 * No jest/vitest dependency required.
 *
 * Tests:
 * 1. Required files exist (app/layout.tsx, app/page.tsx, app/globals.css, etc.)
 * 2. globals.css contains required CSS custom properties.
 * 3. layout.tsx contains data-theme="dark" (dark-first invariant).
 * 4. layout.tsx contains reduced-motion script (accessibility invariant).
 * 5. signal/page.tsx does not render [PROVISIONAL] strings.
 * 6. Public detail/impact routes exist and preserve their public-read boundary.
 * 7. kefe-api.ts does not import admin-only endpoints.
 */

import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = join(__dirname, "..");

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓  ${name}`);
    passed++;
  } catch (err) {
    console.error(`  ✗  ${name}`);
    console.error(`     ${err.message}`);
    failed++;
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function readFile(rel) {
  const abs = join(ROOT, rel);
  assert(existsSync(abs), `File does not exist: ${rel}`);
  return readFileSync(abs, "utf-8");
}

console.log("\nKEFE Web — structural tests\n");

// ---------------------------------------------------------------------------
// 1. Required files exist
// ---------------------------------------------------------------------------

test("app/layout.tsx exists", () => readFile("app/layout.tsx"));
test("app/page.tsx exists", () => readFile("app/page.tsx"));
test("app/globals.css exists", () => readFile("app/globals.css"));
test("app/not-found.tsx exists", () => readFile("app/not-found.tsx"));
test("app/signal/page.tsx exists", () => readFile("app/signal/page.tsx"));
test("app/signal/[signalId]/page.tsx exists", () =>
  readFile("app/signal/[signalId]/page.tsx"),
);
test("app/cases/page.tsx exists", () => readFile("app/cases/page.tsx"));
test("app/cases/[caseId]/page.tsx exists", () => readFile("app/cases/[caseId]/page.tsx"));
test("app/share/[token]/page.tsx exists", () => readFile("app/share/[token]/page.tsx"));
test("app/impact/page.tsx exists", () => readFile("app/impact/page.tsx"));
test("src/components/site-header.tsx exists", () => readFile("src/components/site-header.tsx"));
test("src/lib/kefe-api.ts exists", () => readFile("src/lib/kefe-api.ts"));
test("next.config.ts exists", () => readFile("next.config.ts"));
test("tsconfig.json exists", () => readFile("tsconfig.json"));
test(".env.example exists", () => readFile(".env.example"));

// ---------------------------------------------------------------------------
// 2. globals.css — required design token properties
// ---------------------------------------------------------------------------

test("globals.css: contains dark theme canvas token", () => {
  const css = readFile("app/globals.css");
  assert(css.includes("--kefe-color-canvas"), "Missing --kefe-color-canvas");
});

test("globals.css: contains gold token", () => {
  const css = readFile("app/globals.css");
  assert(css.includes("--kefe-color-gold"), "Missing --kefe-color-gold");
});

test("globals.css: contains reduced-motion override", () => {
  const css = readFile("app/globals.css");
  assert(
    css.includes("prefers-reduced-motion"),
    "Missing prefers-reduced-motion override — accessibility gate failure",
  );
});

test("globals.css: contains light theme section", () => {
  const css = readFile("app/globals.css");
  assert(css.includes('[data-theme="light"]'), "Missing light theme section");
});

// ---------------------------------------------------------------------------
// 3. layout.tsx — dark-first invariant
// ---------------------------------------------------------------------------

test("layout.tsx: dark-first — data-theme=dark on html element", () => {
  const layout = readFile("app/layout.tsx");
  assert(
    layout.includes('data-theme="dark"'),
    'Missing data-theme="dark" on html element — dark-first invariant violation',
  );
});

// ---------------------------------------------------------------------------
// 4. layout.tsx — accessibility: reduced-motion / theme flash prevention
// ---------------------------------------------------------------------------

test("layout.tsx: contains theme flash prevention script", () => {
  const layout = readFile("app/layout.tsx");
  assert(
    layout.includes("kefe-theme"),
    "Missing kefe-theme localStorage script — theme flash prevention required",
  );
});

test("layout.tsx: resolves relative social images against a canonical origin", () => {
  const layout = readFile("app/layout.tsx");
  assert(layout.includes("metadataBase: new URL(siteUrl)"), "Missing metadataBase");
  assert(layout.includes('NEXT_PUBLIC_SITE_URL ?? "https://kefe.app"'),
    "Canonical site URL must have an explicit production-safe fallback");
});

test("next.config.ts: disables framework disclosure and clickjacking", () => {
  const config = readFile("next.config.ts");
  assert(config.includes("poweredByHeader: false"), "X-Powered-By must be disabled");
  assert(config.includes('key: "X-Frame-Options"'), "Missing X-Frame-Options header");
  assert(config.includes('value: "DENY"'), "Public pages must deny framing");
});

test("next.config.ts: prevents MIME sniffing", () => {
  const config = readFile("next.config.ts");
  assert(
    config.includes('key: "X-Content-Type-Options"') && config.includes('value: "nosniff"'),
    "Missing nosniff response header",
  );
});

test("next.config.ts: bounds referrer and browser capability exposure", () => {
  const config = readFile("next.config.ts");
  assert(config.includes('key: "Referrer-Policy"'), "Missing Referrer-Policy header");
  assert(config.includes('key: "Permissions-Policy"'), "Missing Permissions-Policy header");
  for (const capability of ["camera=()", "geolocation=()", "microphone=()"] ) {
    assert(config.includes(capability), `Permissions-Policy must disable ${capability}`);
  }
});

// ---------------------------------------------------------------------------
// 5. signal/page.tsx — does NOT render [PROVISIONAL]
// ---------------------------------------------------------------------------

test("signal/page.tsx: does not hardcode [PROVISIONAL] in JSX output", () => {
  const page = readFile("app/signal/page.tsx");
  // The [PROVISIONAL] guard is in the API; the web page should not render it
  // Note: the word 'PROVISIONAL' may appear in comments, but must not be in
  // rendered JSX string literals
  const jsxProvisional = page.match(/>[^<]*\[PROVISIONAL\][^<]*</);
  assert(
    !jsxProvisional,
    "[PROVISIONAL] found in JSX output — provisional statements must not be publicly rendered",
  );
});

// ---------------------------------------------------------------------------
// 6. Detail and impact routes — public-read boundary
// ---------------------------------------------------------------------------

test("signal detail: encodes the dynamic identifier in public API calls", () => {
  const api = readFile("src/lib/kefe-api.ts");
  assert(
    api.includes("encodeURIComponent(signalId)"),
    "Signal identifiers must be URL-encoded before entering an API path",
  );
});

test("impact page: uses only public list operations", () => {
  const page = readFile("app/impact/page.tsx");
  assert(page.includes("listInstitutionResponses"), "Missing institution response list");
  assert(page.includes("listActionMilestones"), "Missing action milestone list");
  assert(!/\b(create|update|delete|post|patch)\w*\s*\(/i.test(page),
    "Public impact page must not invoke mutation operations");
});

test("impact page: exposes accessible error, progress and navigation landmarks", () => {
  const page = readFile("app/impact/page.tsx");
  assert(page.includes('role="alert"'), "Impact errors must use role=alert");
  assert(page.includes('role="progressbar"'), "Action progress must use role=progressbar");
  assert(page.includes('aria-label="İlgili sayfalar"'), "Impact footer navigation needs a label");
});

test("home page: featured signals link to their detail route", () => {
  const page = readFile("app/page.tsx");
  assert(
    page.includes("/signal/${encodeURIComponent(card.signal_id)}"),
    "Featured signal cards must link to their detail route",
  );
});

test("home page: action progress is semantic rather than presentational", () => {
  const page = readFile("app/page.tsx");
  assert(page.includes('role="progressbar"'), "Home action progress must use role=progressbar");
  assert(!page.includes('role="presentation"'), "Action progress must not be hidden from assistive tech");
  assert(page.includes("clampPercentage"), "External progress values must be clamped");
});

// ---------------------------------------------------------------------------
// 7. kefe-api.ts — no admin/internal endpoints
// ---------------------------------------------------------------------------

test("kefe-api.ts: does not import /internal/ admin endpoints", () => {
  const api = readFile("src/lib/kefe-api.ts");
  const adminPaths = ["/internal/admin/", "/v1/admin/", "/internal/signal-pipeline/"];
  for (const path of adminPaths) {
    assert(
      !api.includes(path),
      `kefe-api.ts contains admin/internal endpoint "${path}" — public client must not expose admin routes`,
    );
  }
});

test("kefe-api.ts: exports listSignalConsensusCards", () => {
  const api = readFile("src/lib/kefe-api.ts");
  assert(api.includes("listSignalConsensusCards"), "Missing listSignalConsensusCards export");
});

test("kefe-api.ts: uses /v1/signals/consensus-cards endpoint", () => {
  const api = readFile("src/lib/kefe-api.ts");
  assert(
    api.includes("/v1/signals/consensus-cards"),
    "Missing /v1/signals/consensus-cards endpoint",
  );
});

test("kefe-api.ts: uses /v1/cases endpoint (not /v1/context)", () => {
  const api = readFile("src/lib/kefe-api.ts");
  assert(api.includes("/v1/cases"), "Missing /v1/cases endpoint");
  assert(!api.includes("/v1/context"), "/v1/context is the wrong endpoint — use /v1/cases");
});

test("kefe-api.ts: exports getPublicShare", () => {
  const api = readFile("src/lib/kefe-api.ts");
  assert(api.includes("getPublicShare"), "Missing getPublicShare export");
});

test("kefe-api.ts: impact client exposes public reads only", () => {
  const api = readFile("src/lib/kefe-api.ts");
  assert(api.includes("listInstitutionResponses"), "Missing institution response reader");
  assert(api.includes("listActionMilestones"), "Missing action milestone reader");
  assert(!api.includes('method: "POST"'), "Public API client must not issue POST requests");
  assert(!api.includes('method: "PATCH"'), "Public API client must not issue PATCH requests");
  assert(!api.includes('method: "DELETE"'), "Public API client must not issue DELETE requests");
});

test("share/[token]/page.tsx: does not expose share token in rendered HTML title", () => {
  const page = readFile("app/share/[token]/page.tsx");
  // Token must NOT appear in static text — only the title from API
  assert(!page.includes("{token}"), "Token must not be rendered directly in the page");
});

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

const total = passed + failed;
console.log(`\n${failed === 0 ? "✓" : "✗"}  ${passed}/${total} tests passed\n`);
if (failed > 0) process.exit(1);
process.exit(0);
