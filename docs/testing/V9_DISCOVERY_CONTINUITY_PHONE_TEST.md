# KEFE v9 Discovery, Activity and Continuity — RC Phone-Test Checklist

This checklist is the human acceptance gate for promoting KEFE v9. The installable binary used here is a prerelease candidate labelled `v9-rcN`; it is not the promoted v9 release. Completing CI alone does not promote a numbered release.

## Candidate provenance

Record before installation:

- Candidate label:
- Candidate commit:
- Mobile CI run:
- API CI run:
- Artifact ID:
- Artifact ZIP SHA-256:
- Extracted APK SHA-256:
- Android package version:

Reject the candidate if its visible label, commit or hash does not match the recorded values.

## Installation and identity

- [ ] Install over the previous test build or perform a clean install when Android signing identity requires it.
- [ ] Confirm the application opens without a crash.
- [ ] Confirm Android identifies the package as a prerelease version such as `0.9.0-rc.1+9`.
- [ ] Confirm the visible identity reads `Product Preview v9-rc1` with the expected short commit.
- [ ] Confirm no screen presents the candidate as the promoted v9 release.

## Canonical primary navigation

- [ ] Confirm exactly four primary destinations are visible: `Keşfet`, `Tartım`, `Aktivite`, `My KEFE`.
- [ ] Confirm each primary destination opens and preserves the bottom navigation shell.
- [ ] Confirm Radar and Atlas are not primary tabs.
- [ ] In Product Preview, open Radar and Atlas from their secondary Explore controls and return to Explore.
- [ ] Confirm production does not expose preview-only Radar or Atlas data.

## Explore discovery

- [ ] Search by a word in a Case title and confirm only matching Cases remain.
- [ ] Search by a word that appears only in a Case summary and confirm it matches.
- [ ] Select at least two different domain filters and confirm results change.
- [ ] Select `Tümü` and confirm the domain filter resets.
- [ ] Combine search and domain filtering and confirm both constraints apply.
- [ ] Enter a query with no match and confirm the dedicated no-result state appears.
- [ ] Clear filters and confirm the full Case collection returns.

## Saved Case continuity

- [ ] Save the featured Case from its bookmark control.
- [ ] Save a regular Case card.
- [ ] Enable `Yalnızca kaydettiklerim` and confirm only saved Cases remain.
- [ ] Unsave a Case and confirm it disappears from the saved-only result.
- [ ] Close and reopen the app and confirm saved Cases persist on the device.

## Activity continuation

- [ ] Open `Aktivite` and confirm `Kaydettiklerin` appears separately from decision history.
- [ ] Confirm saved Case count and titles are correct.
- [ ] Open a saved Case and confirm it uses the canonical `/case/:caseId` journey.
- [ ] Remove a saved Case from Activity and confirm it is removed from Explore saved-only filtering.
- [ ] Confirm recent committed decisions are visible in the decision-history section.
- [ ] Confirm revision and Reflection markers appear when present.
- [ ] Confirm saving or removing a Case does not change weigh, revisit or Reflection counts.

## My KEFE boundary

- [ ] Open `My KEFE` and confirm saved Cases are not listed there.
- [ ] Confirm weigh, revisit, Reflection and domain-activity insights remain visible.
- [ ] Confirm no copy infers personality, ideology, psychometrics or causality.

## Regression, privacy and accessibility

- [ ] Complete one normal Context → Weigh → Commit → Reveal → Perspective journey.
- [ ] Confirm collective results remain hidden before Commit.
- [ ] Confirm production does not substitute preview data after an API failure.
- [ ] Confirm no copy claims account sync or cross-device saved-Case restore.
- [ ] Confirm no analytics or debug output contains raw search text, Case title/summary or private rationale.
- [ ] Confirm TalkBack/Android accessibility announces primary navigation, search, filters, save/remove controls and Activity Case actions.

## Tester record

- Phone/device model:
- Android version:
- Installation method:
- Passed items:
- Failed items:
- Blocking defects:
- Non-blocking observations:
- Tester notes:

## Promotion record

Complete only after all applicable phone-test items pass and blocking defects are resolved:

- Final merge commit:
- Final Mobile CI run:
- Final API CI run:
- Promoted artifact ID:
- Promoted artifact ZIP SHA-256:
- Promoted APK SHA-256:
- Promoted Android package version:
- Visible release label:

v9 is not promoted until the release-candidate gate passes, all applicable human checks pass, blocking feedback is resolved, and the final artifact record is complete.
