import assert from "node:assert/strict";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import {
  StatusBadge,
  WorkspaceStepper
} from "../src/components/workspace-primitives";

test("workspace stepper exposes semantic current-stage navigation", () => {
  const markup = renderToStaticMarkup(
    React.createElement(WorkspaceStepper, { active: "BUNDLE" })
  );

  assert.match(markup, /aria-label="Editoryal çalışma aşamaları"/);
  assert.match(markup, /aria-current="step"/);
  assert.match(markup, /Aday paket/);
  assert.doesNotMatch(markup, /onload=/i);
});

test("status is expressed as text and not by color alone", () => {
  const markup = renderToStaticMarkup(
    React.createElement(StatusBadge, { state: "ACCEPTED" })
  );

  assert.match(markup, />ACCEPTED</);
  assert.match(markup, /aria-label="Durum: ACCEPTED"/);
  assert.match(markup, /data-state="ACCEPTED"/);
});
