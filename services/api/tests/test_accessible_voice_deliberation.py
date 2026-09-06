from __future__ import annotations

from kefe_api.modules.decision.accessible_voice_deliberation import (
    AccessibleVoiceDeliberationService,
    VoiceDeliberationMode,
    VoiceDeliberationResult,
)


def test_accessible_voice_processes_anonymized_dictation() -> None:
    r = AccessibleVoiceDeliberationService.process_voice_session(
        session_id="aud_001",
        mode=VoiceDeliberationMode.ANONYMIZED_VOICE_DICTATION,
        audio_duration_seconds=42.5,
        speech_confidence_score=0.94,
        transcript_preview="Kamu yararı gözetilerek şeffaf bir denetim mekanizması kurulmalı.",
    )

    assert isinstance(r, VoiceDeliberationResult)
    assert r.mode == VoiceDeliberationMode.ANONYMIZED_VOICE_DICTATION
    assert r.is_voiceprint_stripped is True
    assert r.speech_confidence_score == 0.94


def test_accessible_voice_invalid_duration() -> None:
    failed = False
    try:
        AccessibleVoiceDeliberationService.process_voice_session(
            session_id="aud_002",
            mode=VoiceDeliberationMode.AUDIO_BRIEFING_READOUT,
            audio_duration_seconds=0.5,  # < 1.0
            speech_confidence_score=1.50,  # > 1.0
            transcript_preview="Kı",  # < 3
        )
    except ValueError:
        failed = True

    assert failed is True
