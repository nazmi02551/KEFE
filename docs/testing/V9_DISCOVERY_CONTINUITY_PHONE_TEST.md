# KEFE v9 Discovery and Continuity — Phone-Test Checklist

This checklist is the human acceptance gate for promoting the v9 phone-test APK. Completing CI alone does not promote a numbered APK.

## Installation and identity

- [ ] Install over the previous test build or perform a clean install when Android signing identity requires it.
- [ ] Confirm the application opens without a crash.
- [ ] Confirm the visible Product Preview identity is still the current non-promoted build identity until v9 is explicitly released.

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

## My KEFE continuation

- [ ] Open My KEFE / Profil and confirm `Kaydettiklerin` is visually separate from decision-history metrics.
- [ ] Confirm saved Case count and titles are correct.
- [ ] Open a saved Case and confirm it uses the canonical Case journey.
- [ ] Remove a saved Case from My KEFE and confirm it is removed from Explore saved-only filtering.
- [ ] Confirm saving or removing a Case does not change weigh, revisit or reflection counts.

## Regression and safety

- [ ] Complete one normal Context → Weigh → Commit → Reveal → Perspective journey.
- [ ] Confirm collective results remain hidden before Commit.
- [ ] Confirm Product Preview Radar, Atlas and Tartım destinations still open.
- [ ] Confirm production does not substitute preview data after an API failure.
- [ ] Confirm no copy claims account sync or cross-device saved-Case restore.
- [ ] Confirm TalkBack/Android accessibility announces search, filters, save/remove controls and saved Case actions.

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