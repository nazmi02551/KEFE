import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';

class SettingsPersistenceStateSurface extends StatelessWidget {
  const SettingsPersistenceStateSurface({
    required this.message,
    required this.icon,
    required this.isError,
    this.onRetry,
    this.retryLabel,
    this.retryKey,
    super.key,
  });

  final String message;
  final IconData icon;
  final bool isError;
  final VoidCallback? onRetry;
  final String? retryLabel;
  final Key? retryKey;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final accent = isError ? visual.attention : visual.rules;

    return Semantics(
      liveRegion: true,
      container: true,
      label: message,
      child: KefeSurface(
        tone: KefeSurfaceTone.raised,
        accent: accent,
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
        borderRadius: 18,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            ExcludeSemantics(
              child: Icon(icon, color: accent, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.onSurfaceStrong,
                  fontWeight: FontWeight.w700,
                  height: 1.35,
                ),
              ),
            ),
            if (onRetry != null && retryLabel != null) ...[
              const SizedBox(width: 10),
              OutlinedButton(
                key: retryKey,
                onPressed: onRetry,
                child: Text(retryLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
