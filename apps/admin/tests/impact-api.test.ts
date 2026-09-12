import test from "node:test";
import assert from "node:assert/strict";
import {
  listInstitutionResponses,
  listActionMilestones,
  proposeAction,
  updateActionProgress
} from "../src/lib/impact-api";

test("listInstitutionResponses calls GET with params", async () => {
  const calls: string[] = [];
  const mockFetch = (async (url: RequestInfo | URL) => {
    calls.push(url.toString());
    return new Response(JSON.stringify([
      {
        response_id: "RESP-001",
        case_version_id: "CASE-001",
        institution_name: "İzmir Büyükşehir Belediyesi",
        authority_role: "REGULATORY_OVERSIGHT",
        verification_status: "VERIFIED",
        response_type: "POLICY_CHANGE",
        statement: "Toplu taşıma sübvansiyon oranı %60 seviyesine yükseltilecektir.",
        published_at: "2026-09-12T00:00:00Z",
        milestone_date: "2026-10-01T00:00:00Z"
      }
    ]), { status: 200 });
  }) as typeof fetch;

  const responses = await listInstitutionResponses("http://localhost:8000", {
    caseVersionId: "CASE-001",
    limit: 20,
    offset: 0,
    fetchImpl: mockFetch
  });

  assert.equal(calls.length, 1);
  assert.ok(calls[0].includes("case_version_id=CASE-001"));
  assert.equal(responses.length, 1);
  assert.equal(responses[0].verification_status, "VERIFIED");
  assert.equal(responses[0].response_type, "POLICY_CHANGE");
});

test("listActionMilestones calls GET with params", async () => {
  const calls: string[] = [];
  const mockFetch = (async (url: RequestInfo | URL) => {
    calls.push(url.toString());
    return new Response(JSON.stringify([
      {
        action_id: "ACT-001",
        case_version_id: "CASE-001",
        title: "Belediye Meclis Kararı Kabulü",
        description: "Meclis gündemine tarife revizyonu teklifi sunuldu.",
        status: "IN_PROGRESS",
        progress_percentage: 50,
        created_at: "2026-09-12T00:00:00Z",
        institution_response_id: "RESP-001",
        target_completion_date: "2026-11-01T00:00:00Z",
        evidence_summary: "Komisyon raporu yayınlandı.",
        evidence_url: "https://belediye.gov.tr/kararlar/2026-14"
      }
    ]), { status: 200 });
  }) as typeof fetch;

  const actions = await listActionMilestones("http://localhost:8000", {
    caseVersionId: "CASE-001",
    fetchImpl: mockFetch
  });

  assert.equal(calls.length, 1);
  assert.equal(actions.length, 1);
  assert.equal(actions[0].status, "IN_PROGRESS");
  assert.equal(actions[0].progress_percentage, 50);
});

test("proposeAction makes authenticated POST with CSRF", async () => {
  const calls: Array<{ url: string; method: string; headers: HeadersInit; body: string }> = [];
  const mockFetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({
      url: url.toString(),
      method: init?.method ?? "GET",
      headers: init?.headers ?? {},
      body: String(init?.body ?? "")
    });
    return new Response(JSON.stringify({
      action_id: "ACT-002",
      case_version_id: "CASE-001",
      title: "Öğrenci Kartı İndirim Paketi",
      description: "Tüm örgün eğitim öğrencilerine %50 ek sübvansiyon.",
      status: "PROPOSED",
      progress_percentage: 0,
      created_at: "2026-09-12T00:00:00Z",
      institution_response_id: null,
      target_completion_date: null,
      evidence_summary: null,
      evidence_url: null
    }), { status: 201 });
  }) as typeof fetch;

  const action = await proposeAction(
    "http://localhost:8000",
    {
      case_version_id: "CASE-001",
      title: "Öğrenci Kartı İndirim Paketi",
      description: "Tüm örgün eğitim öğrencilerine %50 ek sübvansiyon."
    },
    "csrf-test-token-123",
    mockFetch
  );

  assert.equal(calls.length, 1);
  assert.equal(calls[0].method, "POST");
  assert.equal((calls[0].headers as Record<string, string>)["X-CSRF-Token"], "csrf-test-token-123");
  assert.equal(action.status, "PROPOSED");
  assert.equal(action.title, "Öğrenci Kartı İndirim Paketi");
});

test("updateActionProgress makes authenticated PATCH with CSRF", async () => {
  const calls: Array<{ url: string; method: string; headers: HeadersInit; body: string }> = [];
  const mockFetch = (async (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({
      url: url.toString(),
      method: init?.method ?? "GET",
      headers: init?.headers ?? {},
      body: String(init?.body ?? "")
    });
    return new Response(JSON.stringify({
      action_id: "ACT-001",
      case_version_id: "CASE-001",
      title: "Belediye Meclis Kararı Kabulü",
      description: "Meclis gündemine tarife revizyonu teklifi sunuldu.",
      status: "VERIFIED_COMPLETE",
      progress_percentage: 100,
      created_at: "2026-09-12T00:00:00Z",
      institution_response_id: "RESP-001",
      target_completion_date: "2026-11-01T00:00:00Z",
      evidence_summary: "Resmi Gazete yayımı tamamlandı.",
      evidence_url: "https://belediye.gov.tr/resmi-gazete/2026-99"
    }), { status: 200 });
  }) as typeof fetch;

  const updated = await updateActionProgress(
    "http://localhost:8000",
    "ACT-001",
    {
      case_version_id: "CASE-001",
      progress_percentage: 100,
      status: "VERIFIED_COMPLETE",
      evidence_summary: "Resmi Gazete yayımı tamamlandı.",
      evidence_url: "https://belediye.gov.tr/resmi-gazete/2026-99"
    },
    "csrf-patch-token-456",
    mockFetch
  );

  assert.equal(calls.length, 1);
  assert.equal(calls[0].method, "PATCH");
  assert.equal((calls[0].headers as Record<string, string>)["X-CSRF-Token"], "csrf-patch-token-456");
  assert.equal(updated.progress_percentage, 100);
  assert.equal(updated.status, "VERIFIED_COMPLETE");
});
