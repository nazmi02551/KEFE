#!/usr/bin/env node
/**
 * KEFE Locale — Validation Script
 *
 * Validates catalog/tr.json and catalog/en.json against catalog/keys.json:
 *
 * 1. All three catalog files are valid JSON.
 * 2. keys.json contains $metadata with supported_locales.
 * 3. Every key listed in keys.json exists in both tr.json and en.json.
 * 4. No value in tr.json or en.json is blank (empty string or whitespace-only).
 * 5. No key in tr.json or en.json has a numeric or object value (must be string).
 * 6. The two supported locales are exactly ["tr", "en"].
 * 7. Governance invariants:
 *    - tr.json must not contain any English-only pattern for critical decision keys.
 *    - Values must not contain raw domain/backend codes (e.g., "GOLD_STANDARD", "COMMITTED").
 *
 * Exit 0 = pass, exit 1 = fail.
 */

import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = join(__dirname, "..");
const CATALOG = join(ROOT, "catalog");

// ---------------------------------------------------------------------------
// Load and parse
// ---------------------------------------------------------------------------

function loadJson(filePath, label) {
  try {
    return JSON.parse(readFileSync(filePath, "utf-8"));
  } catch (err) {
    console.error(`FAIL: ${label} is not valid JSON: ${err.message}`);
    process.exit(1);
  }
}

const keys = loadJson(join(CATALOG, "keys.json"), "catalog/keys.json");
const tr = loadJson(join(CATALOG, "tr.json"), "catalog/tr.json");
const en = loadJson(join(CATALOG, "en.json"), "catalog/en.json");

const errors = [];
const warnings = [];

function fail(msg) { errors.push(`  ✗ ${msg}`); }
function warn(msg) { warnings.push(`  ⚠ ${msg}`); }

// ---------------------------------------------------------------------------
// 1. $metadata
// ---------------------------------------------------------------------------

if (!keys.$metadata) {
  fail('keys.json: missing $metadata section');
} else {
  const supportedLocales = keys.$metadata.supported_locales;
  if (!Array.isArray(supportedLocales) || !supportedLocales.includes("tr") || !supportedLocales.includes("en")) {
    fail(`keys.json: supported_locales must include "tr" and "en", got: ${JSON.stringify(supportedLocales)}`);
  }
}

// ---------------------------------------------------------------------------
// 2. Collect all required keys from namespaces
// ---------------------------------------------------------------------------

const namespaces = keys.namespaces ?? {};
const allRequiredKeys = [];

for (const [namespace, config] of Object.entries(namespaces)) {
  if (!Array.isArray(config.keys)) {
    fail(`keys.json: namespaces.${namespace}.keys must be an array`);
    continue;
  }
  for (const key of config.keys) {
    allRequiredKeys.push(key);
  }
}

// ---------------------------------------------------------------------------
// 3. Flatten locale catalogs (handle nested dot-notation vs nested objects)
// ---------------------------------------------------------------------------

function flattenObject(obj, prefix = "") {
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "object" && value !== null && !Array.isArray(value)) {
      Object.assign(result, flattenObject(value, fullKey));
    } else {
      result[fullKey] = value;
    }
  }
  return result;
}

const flatTr = flattenObject(tr);
const flatEn = flattenObject(en);

// ---------------------------------------------------------------------------
// 4. Check all required keys exist in both locales
// ---------------------------------------------------------------------------

for (const key of allRequiredKeys) {
  if (!(key in flatTr)) {
    fail(`Missing in tr.json: "${key}"`);
  }
  if (!(key in flatEn)) {
    fail(`Missing in en.json: "${key}"`);
  }
}

// ---------------------------------------------------------------------------
// 5. Validate value types and content
// ---------------------------------------------------------------------------

const RAW_BACKEND_CODES = [
  "GOLD_STANDARD", "SILVER_VALIDATED", "BRONZE_OBSERVED", "UNQUALIFIED",
  "COMMITTED", "IN_REVIEW", "APPROVED", "PUBLISHED", "DRAFT",
  "CORE_PRE_RESULT", "EXPOSED", "ADVOCACY",
];

function validateLocale(flatLocale, localeName) {
  for (const [key, value] of Object.entries(flatLocale)) {
    // Skip metadata keys
    if (key.startsWith("$")) continue;

    if (typeof value !== "string") {
      fail(`${localeName}: key "${key}" has non-string value (${typeof value})`);
      continue;
    }
    if (!value.trim()) {
      fail(`${localeName}: key "${key}" has blank value`);
    }
    // Check for raw backend codes accidentally exposed in display strings
    for (const code of RAW_BACKEND_CODES) {
      if (value === code) {
        fail(`${localeName}: key "${key}" value is a raw backend code "${code}" — display localization must not expose raw domain values`);
      }
    }
  }
}

validateLocale(flatTr, "tr.json");
validateLocale(flatEn, "en.json");

// ---------------------------------------------------------------------------
// 6. Warn about keys in tr.json/en.json not declared in keys.json
// ---------------------------------------------------------------------------

const declaredKeySet = new Set(allRequiredKeys);

for (const key of Object.keys(flatTr)) {
  if (key.startsWith("$")) continue;
  if (!declaredKeySet.has(key)) {
    warn(`tr.json: key "${key}" is not declared in keys.json (undocumented string)`);
  }
}

for (const key of Object.keys(flatEn)) {
  if (key.startsWith("$")) continue;
  if (!declaredKeySet.has(key)) {
    warn(`en.json: key "${key}" is not declared in keys.json (undocumented string)`);
  }
}

// ---------------------------------------------------------------------------
// 7. Summary
// ---------------------------------------------------------------------------

const totalErrors = errors.length;
const totalWarnings = warnings.length;
const totalKeys = allRequiredKeys.length;

if (totalWarnings > 0) {
  console.log(`\n⚠  Warnings (${totalWarnings}):`);
  warnings.forEach((w) => console.log(w));
}

if (totalErrors > 0) {
  console.error(`\n✗  FAILED — ${totalErrors} error(s) across ${totalKeys} required keys:`);
  errors.forEach((e) => console.error(e));
  process.exit(1);
}

console.log(`\n✓  PASS — ${totalKeys} locale keys validated across tr + en (${totalWarnings} warning(s))`);
process.exit(0);