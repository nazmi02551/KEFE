import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';

class AccountOperationStateSurface extends StatelessWidget {
  const AccountOperationStateSurface.status({
    required this.message,
    super.key,
  }) : retryLabel = null,
       retryButtonKey = null,
       onRetry = null,
       isError = false;

  const AccountOperationStateSurface.error({
    required this.message,
    required this.retryLabel,
    required this.retryButtonKey,
    required this.onRetry,
    super.key,
  }) : isError = true;

  final String message;
  final String? retryLabel;
  final Key? retryButtonKey;
  final VoidCallback? onRetry;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final accent = isError ? visual.attention : visual.gold;
    final icon = isError
        ? Icons.error_outline_rounded
        : Icons.hourglass_top_rounded;

    return KefeSurface(
      tone: KefeSurfaceTone.sunken,
      accent: accent,
      padding: const EdgeInsets.all(13),
      child: Semantics(
        liveRegion: true,
        label: message,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ExcludeSemantics(
                  child: Icon(icon, size: 19, color: accent),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    message,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: isError ? accent : visual.mutedForeground,
                      fontWeight: isError ? FontWeight.w700 : FontWeight.w600,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
            if (isError) ...[
              const SizedBox(height: 10),
              OutlinedButton(
                key: retryButtonKey,
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
