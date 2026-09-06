# ADR-0228: Accessible Voice Deliberation & Audio Interface (CAP-082)

## Status

ACCEPTED

## Context

Citizens with visual impairments, motor disabilities, or low textual literacy require complete audio-first deliberation pipelines including text-to-speech case briefing, voice argument dictation with automated anonymization, and speech-based voting. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides an Accessible Voice Deliberation module compliant with WCAG 2.2 AAA standards.

## Decision

1. **Voice Deliberation Mode Taxonomy**:
   - `AUDIO_BRIEFING_READOUT`: Synthesized voice reading of dilemma and perspectives.
   - `ANONYMIZED_VOICE_DICTATION`: Voice pitch-shifted / phoneme-normalized audio input.
   - `SPEECH_CONFIRMED_VOTE`: Voice-controlled blind-first ballot casting.
2. **Privacy / Voiceprint Invariant**:
   - Audio arguments are pitch-shifted and biometric voiceprints are permanently stripped before storage.

## Consequences

- Delivers full civic inclusion for visually impaired and non-textual citizens.
- Protects participant acoustic anonymity against voice biometric identification.
