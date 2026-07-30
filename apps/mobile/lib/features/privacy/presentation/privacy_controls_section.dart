import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/privacy_controller.dart';

class PrivacyControlsSection extends ConsumerWidget {
  const PrivacyControlsSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!ref.watch(privacyExperienceEnabledProvider)) {
      return const SizedBox.shrink();
    }
    final strings = KefeStrings.of(context);
    final state = ref.watch(privacyControllerProvider);
    final controller = ref.read(privacyControllerProvider.notifier);

    return Card(
      key: const ValueKey('privacy-controls'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.privacy_tip_outlined),
                const SizedBox(width: 10),
                Text(
                  strings.privacyHeading,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(strings.privacyBody),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              key: const ValueKey('privacy-export'),
              onPressed: state.uiState == PrivacyUiState.working
                  ? null
                  : () async {
                      final data = await controller.export();
                      if (data == null || !context.mounted) return;
                      final text = const JsonEncoder.withIndent(
                        '  ',
                      ).convert(data);
                      await Clipboard.setData(ClipboardData(text: text));
                      if (!context.mounted) return;
                      showDialog<void>(
                        context: context,
                        builder: (dialogContext) => AlertDialog(
                          title: Text(strings.privacyExportReady),
                          content: Text(strings.privacyExportCopied),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(dialogContext),
                              child: Text(strings.privacyDone),
                            ),
                          ],
                        ),
                      );
                    },
              icon: const Icon(Icons.download_outlined),
              label: Text(strings.privacyExport),
            ),
            const SizedBox(height: 8),
            TextButton.icon(
              key: const ValueKey('privacy-delete'),
              onPressed: state.uiState == PrivacyUiState.working
                  ? null
                  : () => _confirmDelete(context, ref),
              icon: const Icon(Icons.delete_forever_outlined),
              label: Text(strings.privacyDelete),
            ),
            if (state.errorCode != null) ...[
              const SizedBox(height: 8),
              Text(
                strings.privacyFailure(state.errorCode!),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final strings = KefeStrings.of(context);
    final typed = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(strings.privacyDeleteTitle),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(strings.privacyDeleteBody),
            const SizedBox(height: 12),
            TextField(
              key: const ValueKey('privacy-delete-confirmation'),
              controller: typed,
              autocorrect: false,
              decoration: const InputDecoration(labelText: 'DELETE'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(strings.privacyCancel),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.pop(dialogContext, typed.text.trim() == 'DELETE'),
            child: Text(strings.privacyDeletePermanently),
          ),
        ],
      ),
    );
    typed.dispose();
    if (confirmed != true || !context.mounted) return;
    final deleted = await ref.read(privacyControllerProvider.notifier).delete();
    if (deleted && context.mounted) {
      context.go('/welcome');
    }
  }
}
