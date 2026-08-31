import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/privacy_controller.dart';
import '../application/privacy_export_summary.dart';

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
    final visual = context.kefeVisual;
    final working = state.uiState == PrivacyUiState.working;

    return KefeSurface(
      key: const ValueKey('privacy-controls'),
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
                  child: Icon(
                    Icons.privacy_tip_outlined,
                    color: visual.goldSoft,
                  ),
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
                        strings.privacyHeading,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      strings.privacyBody,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: visual.mutedForeground,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            key: const ValueKey('privacy-export'),
            onPressed: working
                ? null
                : () async {
                    final data = await controller.export();
                    if (data == null || !context.mounted) return;
                    final text = const JsonEncoder.withIndent(
                      '  ',
                    ).convert(data);
                    await Clipboard.setData(ClipboardData(text: text));
                    if (!context.mounted) return;
                    final summary = PrivacyExportSummary.tryParse(data);
                    showDialog<void>(
                      context: context,
                      builder: (dialogContext) => AlertDialog(
                        icon: Icon(
                          Icons.download_done_rounded,
                          color: visual.gold,
                        ),
                        title: Text(strings.privacyExportReady),
                        content: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (summary != null) ...[
                              KefeSurface(
                                key: const ValueKey('privacy-export-summary'),
                                tone: KefeSurfaceTone.sunken,
                                padding: const EdgeInsets.all(14),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      strings.privacyExportSummaryTitle,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleSmall
                                          ?.copyWith(
                                            fontWeight: FontWeight.w800,
                                          ),
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      key: const ValueKey(
                                        'privacy-export-record-count',
                                      ),
                                      strings.privacyExportRecordCount(
                                        summary.totalRecords,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      key: const ValueKey(
                                        'privacy-export-group-count',
                                      ),
                                      strings.privacyExportGroupCount(
                                        summary.nonEmptyDatasetCount,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 14),
                            ],
                            Text(strings.privacyExportCopied),
                          ],
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(dialogContext),
                            child: Text(strings.privacyDone),
                          ),
                        ],
                      ),
                    );
                  },
            icon: working
                ? const Icon(Icons.hourglass_top_rounded)
                : const Icon(Icons.download_outlined),
            label: Text(strings.privacyExport),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            key: const ValueKey('privacy-delete'),
            style: OutlinedButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.error,
              side: BorderSide(
                color: Theme.of(
                  context,
                ).colorScheme.error.withValues(alpha: 0.48),
              ),
            ),
            onPressed: working ? null : () => _confirmDelete(context, ref),
            icon: const Icon(Icons.delete_forever_outlined),
            label: Text(strings.privacyDelete),
          ),
          if (state.errorCode != null) ...[
            const SizedBox(height: 14),
            KefeSurface(
              key: const ValueKey('privacy-error-surface'),
              tone: KefeSurfaceTone.sunken,
              padding: const EdgeInsets.all(14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.error_outline_rounded,
                    color: Theme.of(context).colorScheme.error,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      strings.privacyFailure(state.errorCode!),
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

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    var typed = '';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        icon: Icon(
          Icons.warning_amber_rounded,
          color: Theme.of(context).colorScheme.error,
        ),
        title: Text(strings.privacyDeleteTitle),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(strings.privacyDeleteBody),
            const SizedBox(height: 14),
            TextField(
              key: const ValueKey('privacy-delete-confirmation'),
              autocorrect: false,
              onChanged: (value) => typed = value,
              decoration: InputDecoration(
                labelText: 'DELETE',
                prefixIcon: Icon(
                  Icons.lock_outline_rounded,
                  color: visual.mutedForeground,
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(strings.privacyCancel),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
              foregroundColor: Theme.of(context).colorScheme.onError,
            ),
            onPressed: () =>
                Navigator.pop(dialogContext, typed.trim() == 'DELETE'),
            child: Text(strings.privacyDeletePermanently),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    final deleted = await ref.read(privacyControllerProvider.notifier).delete();
    if (!deleted || !context.mounted) return;
    final receipt = ref.read(privacyControllerProvider).deletion;
    if (receipt == null) return;
    await _showDeletionComplete(
      context,
      isProductPreview: receipt.isProductPreview,
    );
    if (context.mounted) {
      context.go('/welcome');
    }
  }

  Future<void> _showDeletionComplete(
    BuildContext context, {
    required bool isProductPreview,
  }) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final title = isProductPreview
        ? strings.privacyDeletePreviewCompleteTitle
        : strings.privacyDeleteCompleteTitle;
    final body = isProductPreview
        ? strings.privacyDeletePreviewCompleteBody
        : strings.privacyDeleteCompleteBody;
    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => PopScope(
        canPop: false,
        child: AlertDialog(
          key: const ValueKey('privacy-delete-complete'),
          icon: Icon(Icons.check_circle_outline_rounded, color: visual.gold),
          title: Text(title),
          content: Text(body),
          actions: [
            FilledButton(
              key: const ValueKey('privacy-delete-continue'),
              onPressed: () => Navigator.pop(dialogContext),
              child: Text(strings.privacyDeleteContinue),
            ),
          ],
        ),
      ),
    );
  }
}
