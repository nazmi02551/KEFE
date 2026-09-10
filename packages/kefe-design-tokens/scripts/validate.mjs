#!/usr/bin/env node
/**
 * KEFE Design Tokens — Validation Script
 *
 * Validates tokens.json against the following rules:
 * 1. JSON is parseable.
 * 2. Required top-level sections are present: color, typography, spacing, radius, shadow, motion.
 * 3. Both dark and light color themes are present.
 * 4. All required color token names exist in both themes.
 * 5. All color values match valid CSS hex or rgba patterns.
 * 6. No token value is blank or undefined.
 * 7. Design system invariants:
 *    - dark.gold value must be present (KEFE signature accent)
 *    - dark.rules_cyan must be present (Rules/Rights dimension)
 *    - dark.empathy_coral must be present (Empathy/Compassion dimension)
 *    - dark.burgundy must be present (secondary accent)
 *    - All color tokens have a "description" field
 *
 * Exit 0 = pass, exit 1 = fail.
 */

import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const tokensPath = join(__dirname, "..", "tokens.json");

let tokens;
try {
  tokens = JSON.parse(readFileSync(tokensPath, "utf-8"));
} catch (err) {
  console.error(`FAIL: tokens.json is not valid JSON: ${err.message}`);
  process.exit(1);
}

const errors = [];
const warnings = [];

function fail(msg) {
  errors.push(`  ✗ ${msg}`);
}

function warn(msg) {
  warnings.push(`  ⚠ ${msg}`);
}

// ---------------------------------------------------------------------------
// 1. Required top-level sections
// ---------------------------------------------------------------------------

// tokens.json uses "border_radius" not "radius"; accept either
const REQUIRED_SECTIONS = ["color", "typography", "spacing", "shadow", "motion"];
if (!tokens["border_radius"] && !tokens["radius"]) {
  fail('Missing required section: "border_radius" (or "radius")');
}
for (const section of REQUIRED_SECTIONS) {
  if (!tokens[section]) {
    fail(`Missing required section: "${section}"`);
  }
}

// ---------------------------------------------------------------------------
// 2. Color themes
// ---------------------------------------------------------------------------

const colorSection = tokens.color ?? {};
for (const theme of ["dark", "light"]) {
  if (!colorSection[theme]) {
    fail(`Missing color theme: "${theme}"`);
  }
}

// ---------------------------------------------------------------------------
// 3. Required color token names in both themes
// ---------------------------------------------------------------------------

const REQUIRED_COLOR_TOKENS = [
  "canvas",
  "surface",
  "raised",
  "sunken",
  "foreground",
  "muted",
  "gold",
  "gold_subtle",
  "rules_cyan",
  "empathy_coral",
  "burgundy",
  "success",
  "attention",
  "critical",
  "overlay",
];

for (const theme of ["dark", "light"]) {
  const themeTokens = colorSection[theme] ?? {};
  for (const tokenName of REQUIRED_COLOR_TOKENS) {
    if (!themeTokens[tokenName]) {
      fail(`Missing color token: color.${theme}.${tokenName}`);
    }
  }
}

// ---------------------------------------------------------------------------
// 4. Color value format validation
// ---------------------------------------------------------------------------

const HEX_PATTERN = /^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$/;
const RGBA_PATTERN = /^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+/;

function isValidColorValue(value) {
  return HEX_PATTERN.test(value) || RGBA_PATTERN.test(value);
}

for (const theme of ["dark", "light"]) {
  const themeTokens = colorSection[theme] ?? {};
  for (const [name, token] of Object.entries(themeTokens)) {
    if (!token || typeof token !== "object") {
      fail(`color.${theme}.${name}: expected object, got ${typeof token}`);
      continue;
    }
    if (!token.value || !String(token.value).trim()) {
      fail(`color.${theme}.${name}: value is blank`);
    } else if (!isValidColorValue(token.value)) {
      fail(`color.${theme}.${name}: invalid color value "${token.value}"`);
    }
    if (!token.description) {
      warn(`color.${theme}.${name}: missing description`);
    }
  }
}

// ---------------------------------------------------------------------------
// 5. Typography — required font families
// ---------------------------------------------------------------------------

const typo = tokens.typography ?? {};
const fontFamilies = typo.font_family ?? {};
for (const key of ["display", "body", "mono"]) {
  if (!fontFamilies[key]?.value) {
    fail(`Missing typography.font_family.${key}`);
  }
}

// ---------------------------------------------------------------------------
// 6. Spacing — numeric scale keys (tokens.json uses "1"–"20" numeric keys)
// ---------------------------------------------------------------------------

const spacing = tokens.spacing ?? {};
// Require at least the core numeric keys: 1 (4px) through 16 (64px)
const REQUIRED_SPACING_KEYS = ["1", "2", "3", "4", "5", "6", "8", "10", "12", "16"];
for (const key of REQUIRED_SPACING_KEYS) {
  if (!spacing[key]?.value) {
    fail(`Missing spacing.${key}`);
  }
}

// ---------------------------------------------------------------------------
// 7. Radius — "border_radius" section (tokens.json canonical name)
// ---------------------------------------------------------------------------

const radius = tokens.border_radius ?? tokens.radius ?? {};
for (const key of ["xs", "sm", "md", "lg", "xl", "full"]) {
  if (!radius[key]?.value) {
    fail(`Missing border_radius.${key} (or radius.${key})`);
  }
}

// ---------------------------------------------------------------------------
// 8. Motion — reduced-motion support
// ---------------------------------------------------------------------------

const motion = tokens.motion ?? {};
if (!motion.duration) {
  fail(`Missing motion.duration`);
}
if (!motion.easing) {
  fail(`Missing motion.easing`);
}
if (!motion.reduced_motion) {
  warn(`motion.reduced_motion not defined — ensure reduced-motion support is documented`);
}

// ---------------------------------------------------------------------------
// 9. Design system invariants
// ---------------------------------------------------------------------------

const dark = colorSection.dark ?? {};

// Gold must be #C9A84C (KEFE signature) in dark mode
if (dark.gold?.value && dark.gold.value.toUpperCase() !== "#C9A84C") {
  warn(`color.dark.gold value is "${dark.gold.value}" — expected canonical "#C9A84C". Update tokens or this validator.`);
}

// Rules/Rights cyan must be present and warm
if (dark.rules_cyan?.value && dark.rules_cyan.value.toUpperCase() !== "#4ABFCF") {
  warn(`color.dark.rules_cyan value is "${dark.rules_cyan.value}" — expected canonical "#4ABFCF".`);
}

// Empathy coral
if (dark.empathy_coral?.value && dark.empathy_coral.value.toUpperCase() !== "#E07A5F") {
  warn(`color.dark.empathy_coral value is "${dark.empathy_coral.value}" — expected canonical "#E07A5F".`);
}

// Burgundy
if (dark.burgundy?.value && dark.burgundy.value.toUpperCase() !== "#7C2D52") {
  warn(`color.dark.burgundy value is "${dark.burgundy.value}" — expected canonical "#7C2D52".`);
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

const totalErrors = errors.length;
const totalWarnings = warnings.length;

if (totalWarnings > 0) {
  console.log(`\n⚠  Warnings (${totalWarnings}):`);
  warnings.forEach((w) => console.log(w));
}

if (totalErrors > 0) {
  console.error(`\n✗  FAILED — ${totalErrors} error(s):`);
  errors.forEach((e) => console.error(e));
  process.exit(1);
}

console.log(`\n✓  PASS — design tokens validated (${totalWarnings} warning(s))`);
process.exit(0);