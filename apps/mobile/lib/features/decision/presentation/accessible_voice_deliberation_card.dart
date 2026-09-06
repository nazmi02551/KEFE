import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/accessible_voice_deliberation_models.dart';

class AccessibleVoiceDeliberationCard extends StatelessWidget {
  const AccessibleVoiceDeliberationCard({
    required this.voice,
    this.onTap,
    super.key,
  });

  final VoiceDeliberationModel voice;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _modeColor(visual, voice.mode);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('accessible-voice-${voice.sessionId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.mic_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.accVoiceEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _modeLabel(strings, voice.mode),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    '${voice.audioDurationSeconds}s',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                voice.transcriptPreview,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  strings.accVoiceConfidenceLabel((voice.speechConfidenceScore * 100).toInt()),
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: visual.gold,
                  ),
                ),
                if (voice.isVoiceprintStripped)
                  Text(
                    strings.accVoiceVoiceprintLabel,
                    style: const TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF10B981),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _modeColor(KefeVisualSystem visual, VoiceDeliberationModeModel mode) => switch (mode) {
    VoiceDeliberationModeModel.audioBriefingReadout => visual.rules,
    VoiceDeliberationModeModel.anonymizedVoiceDictation => visual.gold,
    VoiceDeliberationModeModel.speechConfirmedVote => const Color(0xFF10B981),
  };

  String _modeLabel(KefeStrings strings, VoiceDeliberationModeModel mode) => switch (mode) {
    VoiceDeliberationModeModel.audioBriefingReadout => strings.accVoiceModeReadout,
    VoiceDeliberationModeModel.anonymizedVoiceDictation => strings.accVoiceModeDictation,
    VoiceDeliberationModeModel.speechConfirmedVote => strings.accVoiceModeVote,
  };
}
