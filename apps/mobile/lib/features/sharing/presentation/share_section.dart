import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/share_controller.dart';

class ShareSection extends ConsumerWidget {
  const ShareSection({required this.sessionId, super.key});

  final String sessionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!ref.watch(shareExperienceEnabledProvider)) {
      return const SizedBox.shrink();
    }
    final strings = KefeStrings.of(context);
    final state = ref.watch(shareControllerProvider);
    final controller = ref.read(shareControllerProvider.notifier);
    final created = state.created;
    final visual = context.kefeVisual;

    return KefeSurface(
      key: const ValueKey('share-section'),
      tone: KefeSurfaceTone.raised,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  color: visual.gold.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: visual.border),
                ),
                child: SizedBox.square(
                  dimension: 42,
                  child: Icon(Icons.ios_share_rounded, color: visual.goldSoft),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Semantics(
                      header: true,
                      child: Text(
                        strings.shareTitle,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      strings.shareCaseOnlyNote,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: visual.mutedForeground,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          if (created == null)
            FilledButton.icon(
              key: const ValueKey('share-create'),
              onPressed: state.uiState == ShareUiState.creating
                  ? null
                  : () => controller.create(sessionId),
              icon: state.uiState == ShareUiState.creating
                  ? const Icon(Icons.hourglass_top_rounded)
                  : const Icon(Icons.link_rounded),
              label: Text(
                state.uiState == ShareUiState.creating
                    ? strings.sharePreparing
                    : strings.shareCreate,
              ),
            )
          else ...[
            KefeSurface(
              key: const ValueKey('share-ready-surface'),
              tone: KefeSurfaceTone.sunken,
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.link_rounded,
                        size: 20,
                        color: visual.goldSoft,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: SelectableText(
                          created.deepLink,
                          key: const ValueKey('share-deep-link'),
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(
                                color: visual.foreground,
                                fontWeight: FontWeight.w700,
                                height: 1.35,
                              ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton.icon(
                          key: const ValueKey('share-copy'),
                          onPressed: () async {
                            await Clipboard.setData(
                              ClipboardData(text: created.deepLink),
                            );
                            if (!context.mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(strings.shareCopied)),
                            );
                          },
                          icon: const Icon(Icons.copy_rounded),
                          label: Text(strings.shareCopy),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton.outlined(
                        key: const ValueKey('share-revoke'),
                        onPressed: controller.revoke,
                        tooltip: strings.shareRevoke,
                        icon: const Icon(Icons.link_off_rounded),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                    key: const ValueKey('share-preview-receiver'),
                    onPressed: () => context.push('/share/${created.token}'),
                    icon: const Icon(Icons.visibility_outlined),
                    label: Text(strings.sharePreviewReceiver),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    strings.shareExternalEntryBoundary,
                    key: const ValueKey('share-external-entry-boundary'),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: visual.mutedForeground,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
          ],
          if (state.errorCode != null) ...[
            const SizedBox(height: 12),
            KefeSurface(
              key: const ValueKey('share-error-surface'),
              tone: KefeSurfaceTone.sunken,
              padding: const EdgeInsets.all(13),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.error_outline_rounded,
                    color: Theme.of(context).colorScheme.error,
                    size: 20,
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      strings.shareFailure(state.errorCode!),
                      key: const ValueKey('share-error'),
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
