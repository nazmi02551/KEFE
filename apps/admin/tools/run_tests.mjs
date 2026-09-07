import { readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(__dirname, "..");
const testsDir = resolve(appRoot, "tests");

const testFiles = readdirSync(testsDir)
  .filter((file) => file.endsWith(".test.ts"))
  .map((file) => resolve(testsDir, file));

const result = spawnSync(
  process.execPath,
  ["--import", "tsx", "--test", ...testFiles],
  {
    cwd: appRoot,
    stdio: "inherit",
  }
);

process.exit(result.status ?? 0);
