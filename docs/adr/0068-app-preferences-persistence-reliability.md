# ADR-0068 — App Preferences Persistence Reliability

**Status:** Accepted  
**Date:** 2026-08-01  
**Issue:** #172  
**Parent:** PR #170 / Slice 29

## Context

`KefeApp` starts `AppPreferencesController.load()` as a fire-and-forget task. The controller previously allowed persistence read exceptions to escape and represented no loading, saving or failure state. `SettingsScreen` therefore rendered default system locale/theme choices before a successful read and locale/theme write failures could leave the optimistic selection visible even though it was not persisted.

This is a reliability and state-truth problem, not a change to the preference model.

## Decision

Introduce an explicit controller-owned preference persistence state while preserving the existing store contract and preference meanings.

The state distinguishes:

- idle: deterministic system defaults before resolution;
- loading: one preferences read is in flight;
- ready: persisted values are known;
- saving: one locale or theme write is in flight;
- error: the latest read or write failed.

Read failures are caught and represented. They do not block app launch; the app continues with deterministic system defaults, while Settings does not present those defaults as trusted persisted values. Retry invokes only the existing store read path.

Locale and theme writes use the current ready state as the last-known persisted snapshot. The selected value may be shown while the write is in flight, but a failure restores that snapshot and exposes a retryable error. Concurrent load/write attempts are rejected by controller guards.

`SettingsScreen` renders deterministic KEFE loading, saving and error disclosures with stable keys and no indeterminate progress.

## Preserved boundaries

- `AppPreferencesStore` interface;
- SharedPreferences keys and enum-name serialization;
- locale choices: system, Turkish, English;
- theme choices: system, light, dark;
- root routes and onboarding behavior;
- Privacy behavior;
- API, schema, migrations and auth;
- production/Product Preview provider isolation.

## Consequences

Preference persistence failures become visible and recoverable. Settings no longer claims a saved selection before a successful read, and failed writes do not leave unsaved values displayed as durable.

This does not prove target-device SharedPreferences reliability or production/store behavior; those remain external evidence gates.
