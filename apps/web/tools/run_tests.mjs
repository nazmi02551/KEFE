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
 * 6. kefe-api.ts does not import admin-only endpoints.
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
// 6. kefe-api.ts — no admin/internal endpoints
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

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

const total = passed + failed;
console.log(`\n${failed === 0 ? "✓" : "✗"}  ${passed}/${total} tests passed\n`);
if (failed > 0) process.exit(1);
process.exit(0);