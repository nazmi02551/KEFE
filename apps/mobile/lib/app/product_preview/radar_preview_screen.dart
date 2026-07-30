import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/design/kefe_theme.dart';
import 'preview_components.dart';

class RadarPreviewScreen extends StatelessWidget {
  const RadarPreviewScreen({super.key});

  static const _items = [
    (
      rank: '1',
      domain: 'TECH · GLOBAL',
      title: 'YZ şirketlerinin kişisel veri toplaması sınırlandırılmalı mı?',
      signal: 'Yükselen tartışma',
      caseId: '11111111-1111-4111-8111-111111111112',
    ),
    (
      rank: '2',
      domain: 'SPORTS',
      title: 'Tartışmalı penaltı kararı doğru muydu?',
      signal: 'Sports CALL',
      caseId: '11111111-1111-4111-8111-111111111113',
    ),
    (
      rank: '3',
      domain: 'WORK',
      title:
          'YZ nedeniyle işten çıkarma öncesi yeniden eğitim zorunlu olmalı mı?',
      signal: 'İş & ekonomi',
      caseId: '11111111-1111-4111-8111-111111111117',
    ),
    (
      rank: '4',
      domain: 'DAILY LIFE',
      title: 'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
      signal: 'Günlük ikilem',
      caseId: '11111111-1111-4111-8111-111111111116',
    ),
    (
      rank: '5',
      domain: 'EDUCATION',
      title: 'Üniversitelerde üretken YZ kullanımı sınırlandırılmalı mı?',
      signal: 'Eğitim',
      caseId: '11111111-1111-4111-8111-111111111118',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          const PreviewPageHeader(
            eyebrow: 'KEFE RADAR',
            title: 'Dünya şu an\nneyi tartışıyor?',
            icon: Icons.radar_rounded,
          ),
          const SizedBox(height: 14),
          const PreviewNotice(
            text:
                'Canlı trend verisi değil · Product Preview için temsili sıralama',
          ),
          const SizedBox(height: 18),
          const Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              PreviewFilterPill(label: 'Trendler', selected: true),
              PreviewFilterPill(label: 'Yükselen'),
              PreviewFilterPill(label: 'Global'),
              PreviewFilterPill(label: 'Senin için'),
            ],
          ),
          const SizedBox(height: 18),
          for (final item in _items) ...[
            Card(
              child: InkWell(
                borderRadius: BorderRadius.circular(20),
                onTap: () => context.push('/case/${item.caseId}'),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 34,
                        height: 34,
                        alignment: Alignment.center,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: KefeColorTokens.gold,
                        ),
                        child: Text(
                          item.rank,
                          style: const TextStyle(
                            color: Color(0xFF171106),
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                      const SizedBox(width: 13),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item.domain,
                              style: Theme.of(context).textTheme.labelSmall
                                  ?.copyWith(
                                    color: KefeColorTokens.goldSoft,
                                    fontWeight: FontWeight.w800,
                                  ),
                            ),
                            const SizedBox(height: 7),
                            Text(
                              item.title,
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(
                                    fontWeight: FontWeight.w800,
                                    height: 1.2,
                                  ),
                            ),
                            const SizedBox(height: 9),
                            Row(
                              children: [
                                Icon(
                                  Icons.trending_up_rounded,
                                  size: 16,
                                  color: Theme.of(context).colorScheme.tertiary,
                                ),
                                const SizedBox(width: 5),
                                Text(
                                  item.signal,
                                  style: Theme.of(context).textTheme.bodySmall
                                      ?.copyWith(
                                        color: KefeColorTokens.textMutedDark,
                                      ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.chevron_right_rounded),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}
