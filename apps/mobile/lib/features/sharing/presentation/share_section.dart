import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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

    return Card(
      key: const ValueKey('share-section'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.ios_share_outlined),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    strings.shareTitle,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(strings.shareCaseOnlyNote),
            const SizedBox(height: 12),
            if (created == null) ...[
              FilledButton.icon(
                key: const ValueKey('share-create'),
                onPressed: state.uiState == ShareUiState.creating
                    ? null
                    : () => controller.create(sessionId),
                icon: const Icon(Icons.link_rounded),
                label: Text(
                  state.uiState == ShareUiState.creating
                      ? strings.sharePreparing
                      : strings.shareCreate,
                ),
              ),
            ] else ...[
              SelectableText(
                created.deepLink,
                key: const ValueKey('share-deep-link'),
              ),
              const SizedBox(height: 10),
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
                  IconButton(
                    key: const ValueKey('share-revoke'),
                    onPressed: controller.revoke,
                    tooltip: strings.shareRevoke,
                    icon: const Icon(Icons.link_off_rounded),
                  ),
                ],
              ),
            ],
            if (state.errorCode != null) ...[
              const SizedBox(height: 10),
              Text(
                strings.shareFailure(state.errorCode!),
                key: const ValueKey('share-error'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
