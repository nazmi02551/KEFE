import assert from "node:assert/strict";
import test from "node:test";

import {
  createFlowStep,
  createFlowTemplate,
  moveItem,
  parseCodeList,
  topologyPreview,
  validateFlowComposerVersion
} from "../src/lib/flow-composer";
import type { FlowComposerVersion } from "../src/lib/flow-composer";

function validVersion(): FlowComposerVersion {
  return {
    id: "33333333-3333-4333-8333-333333333333",
    version_no: 2,
    state: "DRAFT",
    primitives: [
      {
        code: "CONTEXT",
        label_key: "primitive.context",
        payload_schema_ref: null,
        enabled: true
      },
      {
        code: "DECISION",
        label_key: "primitive.decision",
        payload_schema_ref: null,
        enabled: true
      }
    ],
    capabilities: [
      {
        code: "SOURCE_REVEAL",
        label_key: "capability.source_reveal",
        compatible_primitive_codes: ["CONTEXT"],
        config_schema_ref: null,
        enabled: true
      },
      {
        code: "COMMIT_FIRST",
        label_key: "capability.commit_first",
        compatible_primitive_codes: ["DECISION"],
        config_schema_ref: null,
        enabled: true
      }
    ],
    flow_templates: [
      {
        code: "LINEAR",
        version_no: 1,
        label_key: "flow.linear",
        entry_step_code: "CONTEXT",
        enabled: true,
        steps: [
          {
            code: "CONTEXT",
            primitive_code: "CONTEXT",
            capability_codes: ["SOURCE_REVEAL"],
            next_step_codes: ["DECISION"],
            payload_schema_ref: null
          },
          {
            code: "DECISION",
            primitive_code: "DECISION",
            capability_codes: ["COMMIT_FIRST"],
            next_step_codes: [],
            payload_schema_ref: null
          }
        ]
      }
    ],
    created_at: "2026-08-04T18:00:00Z",
    published_at: null,
    cloned_from_version_id: "77777777-7777-4777-8777-777777777777"
  };
}

test("valid generic Flow produces deterministic topology and no problems", () => {
  const version = validVersion();
  assert.deepEqual(validateFlowComposerVersion(version), []);
  assert.deepEqual(topologyPreview(version.flow_templates[0]), [
    "CONTEXT [CONTEXT] → DECISION",
    "DECISION [DECISION] → TERMINAL"
  ]);
});

test("graph validation reports unreachable, cyclic, duplicate and incompatible data", () => {
  const version = validVersion();
  version.flow_templates[0].steps.push({
    code: "ORPHAN",
    primitive_code: "CONTEXT",
    capability_codes: ["COMMIT_FIRST", "COMMIT_FIRST"],
    next_step_codes: [],
    payload_schema_ref: null
  });
  version.flow_templates[0].steps[1].next_step_codes = ["CONTEXT"];
  version.flow_templates.push({ ...version.flow_templates[0] });

  const problems = validateFlowComposerVersion(version).join("\n");
  assert.match(problems, /Yinelenen Flow kimliği/);
  assert.match(problems, /erişilemeyen Step'ler: ORPHAN/);
  assert.match(problems, /döngüsel topoloji/);
  assert.match(problems, /yinelenen Capability COMMIT_FIRST/);
  assert.match(problems, /COMMIT_FIRST, CONTEXT ile uyumlu değildir/);
});

test("disabled Flow may use disabled known references but enabled Flow may not", () => {
  const version = validVersion();
  version.primitives[0].enabled = false;
  version.capabilities[0].enabled = false;

  assert.match(
    validateFlowComposerVersion(version).join("\n"),
    /kullanılabilir Primitive bulunamadı/
  );

  version.flow_templates[0].enabled = false;
  assert.deepEqual(validateFlowComposerVersion(version), []);
});

test("structured helpers create stable defaults, parse lists and reorder immutably", () => {
  const flow = createFlowTemplate(3);
  const step = createFlowStep(4);
  assert.equal(flow.code, "NEW_FLOW_3");
  assert.equal(flow.entry_step_code, "STEP_1");
  assert.equal(flow.enabled, false);
  assert.equal(step.code, "STEP_4");
  assert.deepEqual(parseCodeList(" A, B ,, C "), ["A", "B", "C"]);

  const source = ["A", "B", "C"];
  const moved = moveItem(source, 0, 2);
  assert.deepEqual(moved, ["B", "C", "A"]);
  assert.deepEqual(source, ["A", "B", "C"]);
  assert.deepEqual(moveItem(source, -1, 2), source);
});
