export interface FlowComposerPrimitive {
  code: string;
  label_key: string;
  payload_schema_ref: string | null;
  enabled: boolean;
}

export interface FlowComposerCapability {
  code: string;
  label_key: string;
  compatible_primitive_codes: string[];
  config_schema_ref: string | null;
  enabled: boolean;
}

export interface FlowComposerStep {
  code: string;
  primitive_code: string;
  capability_codes: string[];
  next_step_codes: string[];
  payload_schema_ref: string | null;
}

export interface FlowComposerTemplate {
  code: string;
  version_no: number;
  label_key: string;
  entry_step_code: string;
  steps: FlowComposerStep[];
  enabled: boolean;
}

export interface FlowComposerVersion {
  id: string;
  version_no: number;
  state: string;
  primitives: FlowComposerPrimitive[];
  capabilities: FlowComposerCapability[];
  flow_templates: FlowComposerTemplate[];
  created_at: string;
  published_at: string | null;
  cloned_from_version_id: string | null;
}

export interface FlowComposerSaveInput {
  flow_templates: FlowComposerTemplate[];
}

export interface ConfigurationAuditEntry {
  audit_id: string;
  config_version_id: string;
  actor_ref: string;
  command: string;
  previous_state: string | null;
  new_state: string;
  rationale: string | null;
  occurred_at: string;
}

export interface ConfigurationAuditTrail {
  items: ConfigurationAuditEntry[];
}

function duplicates(values: string[]): string[] {
  const seen = new Set<string>();
  const repeated = new Set<string>();
  for (const value of values) {
    if (seen.has(value)) repeated.add(value);
    seen.add(value);
  }
  return [...repeated].sort();
}

function reachableCodes(flow: FlowComposerTemplate): Set<string> {
  const stepByCode = new Map(flow.steps.map((step) => [step.code, step]));
  const reachable = new Set<string>();
  const pending = [flow.entry_step_code];
  while (pending.length > 0) {
    const code = pending.pop();
    if (!code || reachable.has(code)) continue;
    const step = stepByCode.get(code);
    if (!step) continue;
    reachable.add(code);
    pending.push(...step.next_step_codes);
  }
  return reachable;
}

function hasCycle(flow: FlowComposerTemplate): boolean {
  const stepByCode = new Map(flow.steps.map((step) => [step.code, step]));
  const visiting = new Set<string>();
  const visited = new Set<string>();

  const visit = (code: string): boolean => {
    if (visiting.has(code)) return true;
    if (visited.has(code)) return false;
    const step = stepByCode.get(code);
    if (!step) return false;
    visiting.add(code);
    for (const nextCode of step.next_step_codes) {
      if (visit(nextCode)) return true;
    }
    visiting.delete(code);
    visited.add(code);
    return false;
  };

  return flow.steps.some((step) => visit(step.code));
}

export function validateFlowComposerVersion(
  version: FlowComposerVersion
): string[] {
  const problems: string[] = [];
  const flowKeys = version.flow_templates.map(
    (flow) => `${flow.code}::${flow.version_no}`
  );
  for (const key of duplicates(flowKeys)) {
    problems.push(`Yinelenen Flow kimliği: ${key}`);
  }

  const primitiveByCode = new Map(
    version.primitives.map((primitive) => [primitive.code, primitive])
  );
  const capabilityByCode = new Map(
    version.capabilities.map((capability) => [capability.code, capability])
  );

  for (const flow of version.flow_templates) {
    const flowLabel = `${flow.code || "(kodsuz Flow)"} v${flow.version_no}`;
    if (!flow.code.trim()) problems.push(`${flowLabel}: Flow kodu zorunludur.`);
    if (!Number.isInteger(flow.version_no) || flow.version_no <= 0) {
      problems.push(`${flowLabel}: sürüm numarası pozitif tam sayı olmalıdır.`);
    }
    if (!flow.label_key.trim()) {
      problems.push(`${flowLabel}: label_key zorunludur.`);
    }
    if (flow.steps.length === 0) {
      problems.push(`${flowLabel}: en az bir Step gerekir.`);
      continue;
    }

    const stepCodes = flow.steps.map((step) => step.code);
    for (const code of duplicates(stepCodes)) {
      problems.push(`${flowLabel}: yinelenen Step kodu ${code}.`);
    }
    const stepCodeSet = new Set(stepCodes);
    if (!stepCodeSet.has(flow.entry_step_code)) {
      problems.push(`${flowLabel}: giriş Step'i mevcut değildir.`);
    }
    if (!flow.steps.some((step) => step.next_step_codes.length === 0)) {
      problems.push(`${flowLabel}: en az bir terminal Step gerekir.`);
    }

    for (const step of flow.steps) {
      const stepLabel = `${flowLabel} / ${step.code || "(kodsuz Step)"}`;
      if (!step.code.trim()) problems.push(`${stepLabel}: Step kodu zorunludur.`);
      const primitive = primitiveByCode.get(step.primitive_code);
      if (!primitive || (flow.enabled && !primitive.enabled)) {
        problems.push(`${stepLabel}: kullanılabilir Primitive bulunamadı.`);
      }

      for (const capabilityCode of duplicates(step.capability_codes)) {
        problems.push(`${stepLabel}: yinelenen Capability ${capabilityCode}.`);
      }
      for (const capabilityCode of step.capability_codes) {
        const capability = capabilityByCode.get(capabilityCode);
        if (!capability || (flow.enabled && !capability.enabled)) {
          problems.push(`${stepLabel}: kullanılabilir Capability ${capabilityCode} bulunamadı.`);
          continue;
        }
        if (
          capability.compatible_primitive_codes.length > 0 &&
          !capability.compatible_primitive_codes.includes(step.primitive_code)
        ) {
          problems.push(
            `${stepLabel}: ${capabilityCode}, ${step.primitive_code} ile uyumlu değildir.`
          );
        }
      }

      for (const nextCode of duplicates(step.next_step_codes)) {
        problems.push(`${stepLabel}: yinelenen geçiş hedefi ${nextCode}.`);
      }
      for (const nextCode of step.next_step_codes) {
        if (!stepCodeSet.has(nextCode)) {
          problems.push(`${stepLabel}: bilinmeyen geçiş hedefi ${nextCode}.`);
        }
      }
    }

    if (stepCodeSet.has(flow.entry_step_code)) {
      const reachable = reachableCodes(flow);
      const unreachable = [...stepCodeSet]
        .filter((code) => !reachable.has(code))
        .sort();
      if (unreachable.length > 0) {
        problems.push(
          `${flowLabel}: girişten erişilemeyen Step'ler: ${unreachable.join(", ")}.`
        );
      }
    }
    if (hasCycle(flow)) {
      problems.push(`${flowLabel}: döngüsel topolojiye izin verilmez.`);
    }
  }

  return problems;
}

export function topologyPreview(flow: FlowComposerTemplate): string[] {
  return flow.steps.map((step) => {
    const targets =
      step.next_step_codes.length > 0
        ? step.next_step_codes.join(" · ")
        : "TERMINAL";
    return `${step.code} [${step.primitive_code}] → ${targets}`;
  });
}

export function createFlowTemplate(index: number): FlowComposerTemplate {
  const code = `NEW_FLOW_${index}`;
  return {
    code,
    version_no: 1,
    label_key: `flow.${code.toLowerCase()}`,
    entry_step_code: "STEP_1",
    enabled: false,
    steps: [
      {
        code: "STEP_1",
        primitive_code: "CONTEXT",
        capability_codes: [],
        next_step_codes: [],
        payload_schema_ref: null
      }
    ]
  };
}

export function createFlowStep(index: number): FlowComposerStep {
  return {
    code: `STEP_${index}`,
    primitive_code: "CONTEXT",
    capability_codes: [],
    next_step_codes: [],
    payload_schema_ref: null
  };
}

export function moveItem<T>(items: T[], from: number, to: number): T[] {
  if (from === to || from < 0 || to < 0 || from >= items.length || to >= items.length) {
    return [...items];
  }
  const copy = [...items];
  const removed = copy.splice(from, 1);
  const item = removed[0];
  if (item === undefined) return copy;
  copy.splice(to, 0, item);
  return copy;
}

export function parseCodeList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
