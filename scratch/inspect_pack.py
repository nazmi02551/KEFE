import json
from pathlib import Path

manifest_path = Path("docs/ecosystem_v3.3/KEFE_Documentation_Ecosystem_2026-07-28_v3.3_RECOVERY_R1/REGISTRY/KEFE_MVP_Execution_Pack_v1.0.0.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))

print("=== GOLDEN PATH ===")
print(" -> ".join(data.get("golden_path", [])))

print("\n=== SCREENS ===")
for s in data.get("screens", []):
    print(f"[{s.get('id')}] {s.get('name')} | Capability: {s.get('capability')}")

print("\n=== INVARIANTS ===")
for inv in data.get("invariants", []):
    print(f"- {inv}")
