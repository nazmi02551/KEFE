import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/design/kefe_surface.dart';
import '../../core/design/kefe_visual_system.dart';
import '../../core/localization/kefe_content_localizer.dart';
import 'preview_components.dart';
import 'radar_preview_fixture.dart';
import 'radar_preview_strings.dart';

class RadarPreviewScreen extends ConsumerWidget {
  const RadarPreviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = RadarPreviewStrings.of(context);
    final content = ref.watch(kefeContentLocalizerProvider);
    final locale = Localizations.localeOf(context);

    return SafeArea(
      bottom: false,
      child: ListView(
        key: const ValueKey('radar-preview-list'),
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          PreviewPageHeader(
            eyebrow: strings.eyebrow,
            title: strings.title,
            icon: Icons.radar_rounded,
          ),
          const SizedBox(height: 14),
          PreviewNotice(
            key: const ValueKey('radar-preview-notice'),
            text: strings.notice,
          ),
          const SizedBox(height: 18),
          Wrap(
            key: const ValueKey('radar-preview-views'),
            spacing: 8,
            runSpacing: 8,
            children: [
              PreviewFilterPill(
                key: const ValueKey('radar-view-trends'),
                label: strings.trends,
                selected: true,
              ),
              PreviewFilterPill(
                key: const ValueKey('radar-view-rising'),
                label: strings.rising,
              ),
              PreviewFilterPill(
                key: const ValueKey('radar-view-global'),
                label: strings.global,
              ),
            ],
          ),
          const SizedBox(height: 18),
          for (final item in RadarPreviewFixture.items) ...[
            _RadarRankingCard(
              item: item,
              title: content.text(
                namespace: KefeContentNamespace.caseTitle,
                id: item.caseId,
                locale: locale,
                fallback: item.fallbackTitle,
              ),
              domain: strings.domain(item.domainCode),
              signal: strings.signal(item.signalCode),
              rankSemantics: strings.rankLabel(item.rank),
              onTap: () => context.push('/case/${item.caseId}'),
            ),
            const SizedBox(height: 11),
          ],
        ],
      ),
    );
  }
}

class _RadarRankingCard extends StatelessWidget {
  const _RadarRankingCard({
    required this.item,
    required this.title,
    required this.domain,
    required this.signal,
    required this.rankSemantics,
    required this.onTap,
  });

  final RadarPreviewItem item;
  final String title;
  final String domain;
  final String signal;
  final String rankSemantics;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final accent = _accentForDomain(visual, item.domainCode);
    final featured = item.rank == 1;
    final foreground = featured ? visual.onSurfaceStrong : visual.foreground;
    final muted = featured
        ? visual.onSurfaceStrong.withValues(alpha: 0.68)
        : visual.mutedForeground;

    return Semantics(
      button: true,
      label: title,
      child: KefeSurface(
        tone: featured ? KefeSurfaceTone.premium : KefeSurfaceTone.raised,
        accent: accent,
        padding: EdgeInsets.zero,
        child: InkWell(
          key: ValueKey('radar-item-${item.caseId}'),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(17),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Semantics(
                  label: rankSemantics,
                  child: ExcludeSemantics(
                    child: Container(
                      width: 38,
                      height: 38,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: accent.withValues(alpha: featured ? 0.24 : 0.12),
                        border: Border.all(
                          color: accent.withValues(
                            alpha: featured ? 0.58 : 0.32,
                          ),
                        ),
                        boxShadow: featured
                            ? [
                                BoxShadow(
                                  color: accent.withValues(alpha: 0.16),
                                  blurRadius: 18,
                                ),
                              ]
                            : null,
                      ),
                      child: Text(
                        '${item.rank}',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(
                              color: featured ? visual.goldSoft : accent,
                              fontWeight: FontWeight.w900,
                            ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 13),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        domain,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: featured ? visual.goldSoft : accent,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 0.55,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(
                              color: foreground,
                              fontWeight: FontWeight.w900,
                              height: 1.22,
                            ),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Icon(
                            Icons.trending_up_rounded,
                            size: 16,
                            color: featured ? visual.goldSoft : accent,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              signal,
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(
                                    color: muted,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Icon(
                  Icons.arrow_forward_rounded,
                  color: featured ? visual.goldSoft : muted,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

Color _accentForDomain(KefeVisualTheme visual, String domainCode) =>
    switch (domainCode) {
      'SPORTS' => visual.attention,
      'WORK' => visual.success,
      'DAILY_LIFE' => visual.gold,
      'EDUCATION' => visual.rules,
      _ => visual.rules,
    };
