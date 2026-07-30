# KEFE v9 Discovery, Activity and Continuity — Phone-Test Checklist

This checklist is the human acceptance gate for promoting the v9 phone-test APK. Completing CI alone does not promote a numbered APK.

## Installation and identity

- [ ] Install over the previous test build or perform a clean install when Android signing identity requires it.
- [ ] Confirm the application opens without a crash.
- [ ] Confirm the visible Product Preview identity is still the current non-promoted build identity until v9 is explicitly released.

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

## Promotion record

Record before publishing v9:

- Mobile CI run:
- API CI run:
- Artifact ID:
- Artifact ZIP SHA-256:
- Extracted APK SHA-256:
- Merge commit:
- Phone/device model:
- Android version:
- Tester notes:

v9 is not promoted until all applicable items above are completed and the artifact identity is recorded in the durable checkpoint.
