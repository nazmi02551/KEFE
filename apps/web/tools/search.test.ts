import assert from "node:assert/strict";
import { test } from "node:test";

import { matchesSearchQuery, normalizeSearchText } from "../src/lib/search";

test("normalization handles Turkish dotted and dotless uppercase I", () => {
  assert.equal(normalizeSearchText("İSTANBUL IŞIK"), "istanbul isik");
  assert.equal(normalizeSearchText("istanbul ışık"), "istanbul isik");
});

test("normalization folds Turkish diacritics and repeated whitespace", () => {
  assert.equal(
    normalizeSearchText("  Çevre\n  Görüşü ŞÜPHELİ  "),
    "cevre gorusu supheli",
  );
});

test("search matches every token regardless of field boundaries or order", () => {
  assert.equal(
    matchesSearchQuery("ulaşım İSTANBUL", [
      "İstanbul Büyükşehir",
      "Toplu ulaşım seçenekleri",
    ]),
    true,
  );
  assert.equal(
    matchesSearchQuery("istanbul sağlık", ["İstanbul", "Toplu ulaşım"]),
    false,
  );
});

test("blank and whitespace-only queries match all records", () => {
  assert.equal(matchesSearchQuery("", ["Herhangi bir kayıt"]), true);
  assert.equal(matchesSearchQuery("  \n\t ", []), true);
});

test("query matching is literal and does not interpret regular expressions", () => {
  assert.equal(matchesSearchQuery("[test]", ["Başlık [test]"]), true);
  assert.equal(matchesSearchQuery(".*", ["Başlık"]), false);
});
