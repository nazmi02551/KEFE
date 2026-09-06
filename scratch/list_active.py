from pathlib import Path

active_dir = Path("docs/ecosystem_v3.3/KEFE_Documentation_Ecosystem_2026-07-28_v3.3_RECOVERY_R1/ACTIVE")
print("=== ACTIVE DOCUMENTS IN ECOSYSTEM ===")
for p in sorted(active_dir.glob("*.docx")):
    print(f"- {p.name}")
