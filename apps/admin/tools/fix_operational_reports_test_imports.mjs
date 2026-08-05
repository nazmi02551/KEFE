import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const replacements = [
  {
    file: "tests/operational-reports-api.test.ts",
    from: '"../src/lib/operational-reports-api.ts"',
    to: '"../src/lib/operational-reports-api"'
  },
  {
    file: "tests/operational-reports.test.ts",
    from: '"../src/lib/operational-reports.ts"',
    to: '"../src/lib/operational-reports"'
  }
];

for (const replacement of replacements) {
  const target = path.resolve(root, replacement.file);
  const source = fs.readFileSync(target, "utf8");
  const matches = source.split(replacement.from).length - 1;
  if (matches !== 1) {
    throw new Error(
      `${replacement.file}: expected exactly one ${replacement.from}, found ${matches}`
    );
  }
  fs.writeFileSync(target, source.replace(replacement.from, replacement.to));
  console.log(`Normalized TypeScript import: ${replacement.file}`);
}
