from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "apps/mobile/lib/features/decision/presentation/decision_flow_screen.dart"
REVEAL = ROOT / "apps/mobile/lib/features/decision/presentation/reveal_result_card.dart"

source = DECISION.read_text(encoding="utf-8")

source = source.replace(
    "import '../../../core/design/kefe_theme.dart';\n",
    "",
)

anchor = "import 'reason_input.dart';\n"
addition = "import 'reason_input.dart';\nimport 'reveal_result_card.dart';\n"
if "import 'reveal_result_card.dart';" not in source:
    if anchor not in source:
        raise SystemExit("decision_flow_screen.dart import anchor not found")
    source = source.replace(anchor, addition, 1)

old_call = "        _RevealCard(state: state),\n"
new_call = (
    "        RevealResultCard(\n"
    "          reveal: state.reveal!,\n"
    "          selectedOption: state.selectedOption,\n"
    "        ),\n"
)
if old_call not in source:
    raise SystemExit("legacy Reveal call not found")
source = source.replace(old_call, new_call, 1)

start_marker = "class _RevealCard extends StatelessWidget {"
end_marker = "class _FirstUseCompletionCard extends StatelessWidget {"
start = source.find(start_marker)
end = source.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("legacy Reveal class block markers not found")
source = source[:start] + source[end:]
DECISION.write_text(source, encoding="utf-8")

reveal_source = REVEAL.read_text(encoding="utf-8")
reveal_source = reveal_source.replace("FontWeight.w750", "FontWeight.w700")
reveal_source = reveal_source.replace(
    "value.clamp(0, 1)",
    "value.clamp(0.0, 1.0).toDouble()",
)
REVEAL.write_text(reveal_source, encoding="utf-8")
