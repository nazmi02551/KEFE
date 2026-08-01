import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';

enum ProgressAsyncStateKind { loading, errorRetryable }

class ProgressAsyncStateSurface extends StatelessWidget {
  const ProgressAsyncStateSurface.loading({
    required this.surfaceKey,
    required this.message,
    super.key,
  }) : kind = ProgressAsyncStateKind.loading,
       retryKey = null,
       retryLabel = null,
       onRetry = null;

  const ProgressAsyncStateSurface.error({
    required this.surfaceKey,
    required this.retryKey,
    required this.message,
    required this.retryLabel,
    required this.onRetry,
    super.key,
  }) : kind = ProgressAsyncStateKind.errorRetryable;

  final ProgressAsyncStateKind kind;
  final String surfaceKey;
  final String? retryKey;
  final String message;
  final String? retryLabel;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final loading = kind == ProgressAsyncStateKind.loading;
    final accent = loading ? visual.rules : visual.attention;
    final icon = loading
        ? Icons.hourglass_top_rounded
        : Icons.error_outline_rounded;

    return KefeSurface(
      key: ValueKey(surfaceKey),
      tone: KefeSurfaceTone.raised,
      accent: accent,
      padding: const EdgeInsets.all(16),
      child: Semantics(
        liveRegion: true,
        label: message,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ExcludeSemantics(child: Icon(icon, color: accent, size: 21)),
                const SizedBox(width: 11),
                Expanded(
                  child: Text(
                    message,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: visual.foreground,
                      height: 1.4,
                      fontWeight: loading ? FontWeight.w700 : FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            if (!loading) ...[
              const SizedBox(height: 12),
              OutlinedButton.icon(
                key: ValueKey(retryKey!),
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: Text(retryLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
