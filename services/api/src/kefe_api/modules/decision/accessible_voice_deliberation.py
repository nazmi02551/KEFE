from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VoiceDeliberationMode(StrEnum):
    AUDIO_BRIEFING_READOUT = "AUDIO_BRIEFING_READOUT"
    ANONYMIZED_VOICE_DICTATION = "ANONYMIZED_VOICE_DICTATION"
    SPEECH_CONFIRMED_VOTE = "SPEECH_CONFIRMED_VOTE"


@dataclass(frozen=True, slots=True)
class VoiceDeliberationResult:
    session_id: str
    mode: VoiceDeliberationMode
    audio_duration_seconds: float
    speech_confidence_score: float
    is_voiceprint_stripped: bool
    transcript_preview: str


class AccessibleVoiceDeliberationService:
    @staticmethod
    def process_voice_session(
        *,
        session_id: str,
        mode: VoiceDeliberationMode,
        audio_duration_seconds: float,
        speech_confidence_score: float,
        transcript_preview: str,
    ) -> VoiceDeliberationResult:
        if not 1.0 <= audio_duration_seconds <= 600.0:
            raise ValueError(f"audio_duration_seconds must be in [1.0, 600.0], got {audio_duration_seconds}")
        if not 0.0 <= speech_confidence_score <= 1.0:
            raise ValueError(f"speech_confidence_score must be in [0.0, 1.0], got {speech_confidence_score}")
        if len(transcript_preview.strip()) < 3:
            raise ValueError("transcript_preview must have at least 3 characters")

        # Invariant: voiceprint stripping is strictly enforced for dictation
        is_stripped = True if mode == VoiceDeliberationMode.ANONYMIZED_VOICE_DICTATION else False

        return VoiceDeliberationResult(
            session_id=session_id.strip(),
            mode=mode,
            audio_duration_seconds=round(audio_duration_seconds, 1),
            speech_confidence_score=round(speech_confidence_score, 2),
            is_voiceprint_stripped=is_stripped,
            transcript_preview=transcript_preview.strip(),
        )
