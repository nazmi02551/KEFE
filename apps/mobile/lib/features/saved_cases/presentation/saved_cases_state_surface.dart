import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';

class SavedCasesStateSurface extends StatelessWidget {
  const SavedCasesStateSurface.loading({
    required this.message,
    this.compact = false,
    super.key,
  }) : retryLabel = null,
       retryButtonKey = null,
       onRetry = null,
       isError = false;

  const SavedCasesStateSurface.error({
    required this.message,
    required this.retryLabel,
    required this.retryButtonKey,
    required this.onRetry,
    this.compact = false,
    super.key,
  }) : isError = true;

  final String message;
  final String? retryLabel;
  final Key? retryButtonKey;
  final VoidCallback? onRetry;
  final bool isError;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final accent = isError ? visual.attention : visual.gold;
    final icon = isError
        ? Icons.cloud_off_outlined
        : Icons.hourglass_top_rounded;

    return KefeSurface(
      tone: KefeSurfaceTone.sunken,
      accent: accent,
      padding: EdgeInsets.all(compact ? 11 : 13),
      child: Semantics(
        liveRegion: true,
        label: message,
        child: isError
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ExcludeSemantics(
                        child: Icon(icon, size: 18, color: accent),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          message,
                          style: Theme.of(context).textTheme.bodySmall
                              ?.copyWith(
                                color: visual.mutedForeground,
                                height: 1.4,
                              ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  OutlinedButton(
                    key: retryButtonKey,
                    onPressed: onRetry,
                    child: Text(retryLabel!),
                  ),
                ],
              )
            : Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ExcludeSemantics(
                    child: Icon(icon, size: 18, color: accent),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      message,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
