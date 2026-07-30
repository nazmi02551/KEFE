import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../application/privacy_controller.dart';

class PrivacyControlsSection extends ConsumerWidget {
  const PrivacyControlsSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!ref.watch(privacyExperienceEnabledProvider)) {
      return const SizedBox.shrink();
    }
    final tr = Localizations.localeOf(context).languageCode == 'tr';
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
                  tr ? 'Verilerin ve gizliliğin' : 'Your data and privacy',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              tr
                  ? 'Kendi ürün geçmişinin makine-okunur kopyasını alabilir veya hesabındaki/misafir kimliğindeki özel verileri silebilirsin.'
                  : 'Export a machine-readable copy of your product history or delete private data attached to your account/guest identity.',
            ),
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
                          title: Text(
                            tr
                                ? 'Veri kopyan hazır'
                                : 'Your data copy is ready',
                          ),
                          content: Text(
                            tr
                                ? 'Makine-okunur JSON panoya kopyalandı. Güvenlik tokenları ve başka kullanıcıların verileri bu dışa aktarıma dahil değildir.'
                                : 'Machine-readable JSON was copied to the clipboard. Security tokens and other users’ data are excluded.',
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(dialogContext),
                              child: Text(tr ? 'Tamam' : 'OK'),
                            ),
                          ],
                        ),
                      );
                    },
              icon: const Icon(Icons.download_outlined),
              label: Text(tr ? 'Verilerimi dışa aktar' : 'Export my data'),
            ),
            const SizedBox(height: 8),
            TextButton.icon(
              key: const ValueKey('privacy-delete'),
              onPressed: state.uiState == PrivacyUiState.working
                  ? null
                  : () => _confirmDelete(context, ref),
              icon: const Icon(Icons.delete_forever_outlined),
              label: Text(tr ? 'Verilerimi sil' : 'Delete my data'),
            ),
            if (state.errorCode != null) ...[
              const SizedBox(height: 8),
              Text(
                '${tr ? 'Gizlilik işlemi başarısız' : 'Privacy action failed'} · ${state.errorCode}',
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final tr = Localizations.localeOf(context).languageCode == 'tr';
    final typed = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          tr ? 'Verileri kalıcı olarak sil?' : 'Delete data permanently?',
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              tr
                  ? 'Bu işlem geri alınamaz. Devam etmek için DELETE yaz.'
                  : 'This cannot be undone. Type DELETE to continue.',
            ),
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
            child: Text(tr ? 'Vazgeç' : 'Cancel'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.pop(dialogContext, typed.text.trim() == 'DELETE'),
            child: Text(tr ? 'Kalıcı olarak sil' : 'Delete permanently'),
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
