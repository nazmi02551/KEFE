#!/usr/bin/env node
/**
 * KEFE test-fixtures validate script
 *
 * Validates that all fixture files declared in package.json exports exist,
 * are valid JSON, and contain required structural fields.
 *
 * Run: node packages/kefe-test-fixtures/scripts/validate.mjs
 * Exit 0 on success, 1 on failure.
 */

import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join, resolve } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, "..");
const FIXTURES_DIR = join(ROOT, "fixtures");

let warnings = 0;
let errors = 0;

function warn(msg) {
  console.warn(`  ⚠  ${msg}`);
  warnings++;
}

function fail(msg) {
  console.error(`  ✗  ${msg}`);
  errors++;
}

function pass(msg) {
  console.log(`  ✓  ${msg}`);
}

function readJson(rel) {
  const abs = join(FIXTURES_DIR, rel);
  if (!existsSync(abs)) {
    fail(`File missing: fixtures/${rel}`);
    return null;
  }
  try {
    return JSON.parse(readFileSync(abs, "utf-8"));
  } catch (e) {
    fail(`Invalid JSON in fixtures/${rel}: ${e.message}`);
    return null;
  }
}

function assertField(obj, path, label) {
  const parts = path.split(".");
  let cur = obj;
  for (const p of parts) {
    if (cur == null || typeof cur !== "object" || !(p in cur)) {
      fail(`${label}: missing field "${path}"`);
      return false;
    }
    cur = cur[p];
  }
  return true;
}

function isValidUUID(str) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(str);
}

console.log("\nKEFE test-fixtures — validate\n");

// ---------------------------------------------------------------------------
// 1. index.json
// ---------------------------------------------------------------------------

const index = readJson("index.json");
if (index) {
  assertField(index, "$metadata.version", "index.json");
  assertField(index, "canonical_uuids.cases", "index.json");
  assertField(index, "canonical_uuids.signals", "index.json");
  assertField(index, "canonical_uuids.actors", "index.json");
  assertField(index, "canonical_uuids.sessions", "index.json");

  // UUID format check on canonical entries
  const allUuids = [
    ...Object.values(index.canonical_uuids?.cases ?? {}),
    ...Object.values(index.canonical_uuids?.signals ?? {}),
    ...Object.values(index.canonical_uuids?.actors ?? {}),
    ...Object.values(index.canonical_uuids?.sessions ?? {}),
  ];
  for (const uuid of allUuids) {
    if (!isValidUUID(uuid)) {
      fail(`index.json: "${uuid}" is not a valid v4 UUID`);
    }
  }
  pass(`index.json: ${allUuids.length} canonical UUIDs validated`);
}

// ---------------------------------------------------------------------------
// 2. signals.json
// ---------------------------------------------------------------------------

const signalsData = readJson("signals.json");
if (signalsData) {
  const signals = signalsData.signals;
  if (!Array.isArray(signals) || signals.length === 0) {
    fail("signals.json: signals array is empty or missing");
  } else {
    let ok = 0;
    for (const s of signals) {
      const base = `signals.json[${s.signal_id ?? "?"}]`;
      let valid = true;
      for (const f of ["signal_id", "case_version_id", "qualification_tier", "agreement_percentage", "sample_size", "dispatch_status"]) {
        if (!(f in s)) { fail(`${base}: missing field "${f}"`); valid = false; }
      }
      if (valid) {
        if (!isValidUUID(s.signal_id)) fail(`${base}: invalid signal_id UUID`);
        if (!isValidUUID(s.case_version_id)) fail(`${base}: invalid case_version_id UUID`);
        if (!["GOLD_STANDARD","SILVER_VALIDATED","BRONZE_OBSERVED","UNQUALIFIED"].includes(s.qualification_tier)) {
          warn(`${base}: unknown qualification_tier "${s.qualification_tier}"`);
        }
        if (typeof s.agreement_percentage !== "number" || s.agreement_percentage < 0 || s.agreement_percentage > 100) {
          fail(`${base}: agreement_percentage must be 0–100`);
        }
        if (typeof s.sample_size !== "number" || s.sample_size < 1) {
          fail(`${base}: sample_size must be ≥1`);
        }
        ok++;
      }
    }
    pass(`signals.json: ${ok}/${signals.length} signal records valid`);
  }
}

// ---------------------------------------------------------------------------
// 3. cases.json
// ---------------------------------------------------------------------------

const casesData = readJson("cases.json");
if (casesData) {
  const cases = casesData.cases;
  if (!Array.isArray(cases) || cases.length === 0) {
    fail("cases.json: cases array is empty or missing");
  } else {
    let ok = 0;
    for (const c of cases) {
      const base = `cases.json[${c.case_id ?? "?"}]`;
      let valid = true;
      for (const f of ["case_id", "case_version_id", "version_no", "primary_domain_code", "state"]) {
        if (!(f in c)) { fail(`${base}: missing field "${f}"`); valid = false; }
      }
      if (valid) {
        if (!isValidUUID(c.case_id)) fail(`${base}: invalid case_id UUID`);
        if (!isValidUUID(c.case_version_id)) fail(`${base}: invalid case_version_id UUID`);
        ok++;
      }
    }
    pass(`cases.json: ${ok}/${cases.length} case records valid`);
  }
}

// ---------------------------------------------------------------------------
// 4. identities.json
// ---------------------------------------------------------------------------

const identitiesData = readJson("identities.json");
if (identitiesData) {
  const actors = identitiesData.actors;
  const sessions = identitiesData.sessions;
  if (!Array.isArray(actors) || actors.length === 0) {
    fail("identities.json: actors array is empty or missing");
  } else {
    let ok = 0;
    for (const a of actors) {
      if (!isValidUUID(a.actor_id)) { fail(`identities.json actor: invalid UUID "${a.actor_id}"`); continue; }
      if (!["REGISTERED","GUEST"].includes(a.actor_type)) {
        warn(`identities.json actor ${a.actor_id}: unknown actor_type "${a.actor_type}"`);
      }
      ok++;
    }
    pass(`identities.json: ${ok}/${actors.length} actor records valid`);
  }
  if (!Array.isArray(sessions) || sessions.length === 0) {
    fail("identities.json: sessions array is empty or missing");
  } else {
    let ok = 0;
    for (const s of sessions) {
      if (!isValidUUID(s.session_id)) { fail(`identities.json session: invalid UUID "${s.session_id}"`); continue; }
      if (!["CORE_PRE_RESULT","EXPOSED"].includes(s.contribution_class)) {
        fail(`identities.json session ${s.session_id}: invalid contribution_class "${s.contribution_class}"`);
      }
      ok++;
    }
    pass(`identities.json: ${ok}/${sessions.length} session records valid`);
  }
}

// ---------------------------------------------------------------------------
// 5. impact.json
// ---------------------------------------------------------------------------

const impactData = readJson("impact.json");
if (impactData) {
  const responses = impactData.institution_responses;
  const milestones = impactData.action_milestones;
  if (!Array.isArray(responses)) {
    fail("impact.json: institution_responses array missing");
  } else {
    let ok = 0;
    for (const r of responses) {
      if (!isValidUUID(r.response_id)) { fail(`impact.json response: invalid UUID "${r.response_id}"`); continue; }
      if (!isValidUUID(r.signal_id)) { fail(`impact.json response: invalid signal_id "${r.signal_id}"`); continue; }
      ok++;
    }
    pass(`impact.json: ${ok}/${responses.length} institution response records valid`);
  }
  if (!Array.isArray(milestones)) {
    fail("impact.json: action_milestones array missing");
  } else {
    let ok = 0;
    for (const m of milestones) {
      if (!isValidUUID(m.milestone_id)) { fail(`impact.json milestone: invalid UUID "${m.milestone_id}"`); continue; }
      ok++;
    }
    pass(`impact.json: ${ok}/${milestones.length} action milestone records valid`);
  }
}

// ---------------------------------------------------------------------------
// 6. Cross-reference: index UUIDs must appear in their respective files
// ---------------------------------------------------------------------------

if (index && signalsData && casesData) {
  const indexCaseUuids = new Set(Object.values(index.canonical_uuids?.cases ?? {}));
  const fixturesCaseUuids = new Set((casesData.cases ?? []).map(c => c.case_id));
  for (const uuid of indexCaseUuids) {
    if (!fixturesCaseUuids.has(uuid)) {
      warn(`index.json canonical case UUID ${uuid} not found in cases.json`);
    }
  }

  const indexSignalUuids = new Set(Object.values(index.canonical_uuids?.signals ?? {}));
  const fixturesSignalUuids = new Set((signalsData.signals ?? []).map(s => s.signal_id));
  for (const uuid of indexSignalUuids) {
    if (!fixturesSignalUuids.has(uuid)) {
      warn(`index.json canonical signal UUID ${uuid} not found in signals.json`);
    }
  }

  if (indexCaseUuids.size > 0 && indexSignalUuids.size > 0) {
    pass(`cross-reference: index UUIDs verified against cases.json and signals.json`);
  }
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

const total = errors + warnings;
if (errors === 0) {
  console.log(`\n✓  PASS — test fixtures validated (${warnings} warning(s))\n`);
  process.exit(0);
} else {
  console.error(`\n✗  FAIL — ${errors} error(s), ${warnings} warning(s)\n`);
  process.exit(1);
}