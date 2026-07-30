import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/share_controller.dart';

class ShareSection extends ConsumerWidget {
  const ShareSection({required this.sessionId, super.key});

  final String sessionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!ref.watch(shareExperienceEnabledProvider)) {
      return const SizedBox.shrink();
    }
    final tr = Localizations.localeOf(context).languageCode == 'tr';
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
                    tr ? 'Bu vakayı paylaş' : 'Share this case',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              tr
                  ? 'MVP paylaşımı yalnız vakayı içerir. Kararın, güven puanın ve özel gerekçen bağlantıya eklenmez.'
                  : 'MVP sharing is case-only. Your decision, confidence, and private reason are never included in the link.',
            ),
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
                      ? (tr ? 'Bağlantı hazırlanıyor…' : 'Preparing link…')
                      : (tr ? 'Vaka bağlantısı oluştur' : 'Create case link'),
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
                          SnackBar(
                            content: Text(
                              tr ? 'Bağlantı kopyalandı.' : 'Link copied.',
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.copy_rounded),
                      label: Text(tr ? 'Kopyala' : 'Copy'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    key: const ValueKey('share-revoke'),
                    onPressed: controller.revoke,
                    tooltip: tr ? 'Bağlantıyı iptal et' : 'Revoke link',
                    icon: const Icon(Icons.link_off_rounded),
                  ),
                ],
              ),
            ],
            if (state.errorCode != null) ...[
              const SizedBox(height: 10),
              Text(
                '${tr ? 'Paylaşım oluşturulamadı' : 'Share failed'} · ${state.errorCode}',
                key: const ValueKey('share-error'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
