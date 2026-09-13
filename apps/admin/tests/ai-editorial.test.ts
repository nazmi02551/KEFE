import test from "node:test";
import assert from "node:assert/strict";
import { AiEditorialApiClient } from "../src/lib/ai-editorial-api";

test("AiEditorialApiClient extracts claims with confidence and type (CAP-060)", async () => {
  const client = new AiEditorialApiClient();
  const res = await client.extractClaims(
    "Resmi verilere göre enerji maliyetleri bu yıl yüzde 25 arttı. Belediyeler toplu taşımayı sübvanse etmek zorundadır."
  );

  assert.ok(res.extracted_claims.length > 0);
  assert.equal(res.extracted_claims[0].claim_type, "FACTUAL");
  assert.ok(res.model_used);
  assert.ok(res.editorial_disclaimer.includes("mandatory human editorial approval"));
});

test("AiEditorialApiClient suggests balanced thesis, antithesis and bridge perspectives", async () => {
  const client = new AiEditorialApiClient();
  const res = await client.suggestPerspectives(
    "Şehir Merkezinde Özel Araç Girişi",
    "Trafiği rahatlatmak ve karbon salınımını düşürmek için ücretlendirme planı."
  );

  assert.equal(res.perspectives.length, 3);
  const orientations = res.perspectives.map((p) => p.orientation);
  assert.ok(orientations.includes("THESIS"));
  assert.ok(orientations.includes("ANTITHESIS"));
  assert.ok(orientations.includes("SYNTHESIS_BRIDGE"));
});

test("AiEditorialApiClient detects biased loaded terms and suggests neutral alternatives", async () => {
  const client = new AiEditorialApiClient();
  const res = await client.checkBias(
    "Alınan bu karar tam bir rezalet olarak değerlendirilmiştir."
  );

  assert.equal(res.is_neutral, false);
  assert.ok(res.flagged_terms.includes("rezalet"));
  assert.equal(res.suggested_neutral_rephrasings["rezalet"], "tartışmalı durum");
});

test("AiEditorialApiClient composes non-normative summary within character limit", async () => {
  const client = new AiEditorialApiClient();
  const raw =
    "Karayolları Genel Müdürlüğü tarafından yürütülen çalışmalar sonucunda kış buzlanma riskine karşı yeni sensör ağları kuruldu.";
  const res = await client.composeSummary(raw, 80);

  assert.ok(res.character_count <= 80);
  assert.ok(res.composed_summary);
});
