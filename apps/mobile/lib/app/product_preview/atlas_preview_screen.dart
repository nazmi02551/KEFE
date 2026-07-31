import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/design/kefe_surface.dart';
import '../../core/design/kefe_visual_system.dart';
import '../../core/localization/kefe_content_localizer.dart';
import 'atlas_globe_visual.dart';
import 'atlas_preview_fixture.dart';
import 'atlas_preview_strings.dart';
import 'preview_components.dart';

class AtlasPreviewScreen extends ConsumerWidget {
  const AtlasPreviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = AtlasPreviewStrings.of(context);
    final content = ref.watch(kefeContentLocalizerProvider);
    final locale = Localizations.localeOf(context);
    final selectedCaseTitle = content.text(
      namespace: KefeContentNamespace.caseTitle,
      id: AtlasPreviewFixture.selectedCaseId,
      locale: locale,
      fallback: AtlasPreviewFixture.selectedCaseFallbackTitle,
    );
    final size = MediaQuery.sizeOf(context);
    final compact = size.width < 340 || size.height < 700;

    return SafeArea(
      bottom: false,
      child: ListView(
        key: const ValueKey('atlas-preview-list'),
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          PreviewPageHeader(
            eyebrow: strings.eyebrow,
            title: strings.title,
            icon: Icons.public_rounded,
          ),
          const SizedBox(height: 14),
          PreviewNotice(
            key: const ValueKey('atlas-preview-notice'),
            text: strings.notice,
          ),
          const SizedBox(height: 18),
          _AtlasHero(
            selectedCaseTitle: selectedCaseTitle,
            strings: strings,
            compact: compact,
          ),
          const SizedBox(height: 24),
          Text(
            strings.countryAverages,
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 12),
          _CountryGrid(strings: strings),
        ],
      ),
    );
  }
}

class _AtlasHero extends StatelessWidget {
  const _AtlasHero({
    required this.selectedCaseTitle,
    required this.strings,
    required this.compact,
  });

  final String selectedCaseTitle;
  final AtlasPreviewStrings strings;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('atlas-hero'),
      tone: KefeSurfaceTone.premium,
      accent: visual.gold,
      padding: EdgeInsets.all(compact ? 14 : 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _SelectedCaseHeader(
            selectedCaseTitle: selectedCaseTitle,
            strings: strings,
          ),
          SizedBox(height: compact ? 13 : 17),
          Row(
            children: [
              Expanded(
                child: Divider(
                  color: visual.gold.withValues(alpha: 0.25),
                  height: 1,
                ),
              ),
              const SizedBox(width: 9),
              Icon(
                Icons.diamond_outlined,
                size: 12,
                color: visual.goldSoft.withValues(alpha: 0.82),
              ),
              const SizedBox(width: 9),
              Text(
                strings.worldView,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: visual.goldSoft,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 0.45,
                ),
              ),
              const SizedBox(width: 9),
              Icon(
                Icons.diamond_outlined,
                size: 12,
                color: visual.goldSoft.withValues(alpha: 0.82),
              ),
              const SizedBox(width: 9),
              Expanded(
                child: Divider(
                  color: visual.gold.withValues(alpha: 0.25),
                  height: 1,
                ),
              ),
            ],
          ),
          SizedBox(height: compact ? 4 : 8),
          AtlasGlobeVisual(markers: _atlasMarkers, compact: compact),
          SizedBox(height: compact ? 4 : 9),
          _AtlasContinuum(strings: strings),
        ],
      ),
    );
  }
}

class _SelectedCaseHeader extends StatelessWidget {
  const _SelectedCaseHeader({
    required this.selectedCaseTitle,
    required this.strings,
  });

  final String selectedCaseTitle;
  final AtlasPreviewStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: visual.gold.withValues(alpha: 0.12),
            border: Border.all(
              color: visual.goldSoft.withValues(alpha: 0.30),
            ),
            boxShadow: [
              BoxShadow(
                color: visual.gold.withValues(alpha: 0.08),
                blurRadius: 14,
              ),
            ],
          ),
          child: Icon(Icons.public_rounded, color: visual.goldSoft, size: 24),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                strings.selectedCase,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: visual.goldSoft,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                selectedCaseTitle,
                key: const ValueKey('atlas-selected-case-title'),
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: visual.onSurfaceStrong,
                  fontWeight: FontWeight.w900,
                  height: 1.25,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CountryGrid extends StatelessWidget {
  const _CountryGrid({required this.strings});

  final AtlasPreviewStrings strings;

  @override
  Widget build(BuildContext context) {
    final textScale = MediaQuery.textScalerOf(context).scale(1);
    return LayoutBuilder(
      builder: (context, constraints) {
        final oneColumn = constraints.maxWidth < 350 || textScale > 1.28;
        return GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: oneColumn ? 1 : 2,
            childAspectRatio: oneColumn ? 2.55 : 1.18,
            crossAxisSpacing: 11,
            mainAxisSpacing: 11,
          ),
          itemCount: AtlasPreviewFixture.countries.length,
          itemBuilder: (context, index) {
            final item = AtlasPreviewFixture.countries[index];
            return _CountryAverageCard(
              countryCode: item.countryCode,
              country: strings.country(item.countryCode),
              value: item.value,
              averageLabel: strings.average,
            );
          },
        );
      },
    );
  }
}

class _AtlasContinuum extends StatelessWidget {
  const _AtlasContinuum({required this.strings});

  final AtlasPreviewStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                strings.rulesRights,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: visual.rules,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
            Expanded(
              child: Text(
                strings.empathyCompassion,
                textAlign: TextAlign.end,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: visual.empathy,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 7),
        const _ScaleTrack(value: null),
        const SizedBox(height: 7),
        Row(
          children: [
            Text(
              '0',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.onSurfaceStrong.withValues(alpha: 0.70),
              ),
            ),
            Expanded(
              child: Text(
                strings.scaleHelper,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: visual.onSurfaceStrong.withValues(alpha: 0.62),
                ),
              ),
            ),
            Text(
              '10',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.onSurfaceStrong.withValues(alpha: 0.70),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _CountryAverageCard extends StatelessWidget {
  const _CountryAverageCard({
    required this.countryCode,
    required this.country,
    required this.value,
    required this.averageLabel,
  });

  final String countryCode;
  final String country;
  final double value;
  final String averageLabel;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final formattedValue = value.toStringAsFixed(1);
    final accent = _countryValueColor(visual, value);
    return Semantics(
      container: true,
      label: '$country · $averageLabel $formattedValue / 10',
      child: KefeSurface(
        key: ValueKey('atlas-country-card-$countryCode'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(15),
        borderRadius: 18,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Row(
              children: [
                Container(
                  width: 31,
                  height: 31,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: accent.withValues(
                      alpha: visual.isDark ? 0.13 : 0.08,
                    ),
                    border: Border.all(color: accent.withValues(alpha: 0.52)),
                  ),
                  child: ExcludeSemantics(
                    child: Text(
                      countryCode,
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: accent,
                        fontSize: 9,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    country,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: Text(
                    averageLabel,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
                Text(
                  formattedValue,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: accent,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            _ScaleTrack(value: value),
          ],
        ),
      ),
    );
  }
}

class _ScaleTrack extends StatelessWidget {
  const _ScaleTrack({required this.value});

  final double? value;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return ExcludeSemantics(
      child: LayoutBuilder(
        builder: (context, constraints) {
          const markerSize = 11.0;
          final normalized = ((value ?? 0) / 10).clamp(0.0, 1.0);
          return SizedBox(
            height: value == null ? 8 : 13,
            child: Stack(
              clipBehavior: Clip.none,
              alignment: Alignment.centerLeft,
              children: [
                Container(
                  height: 7,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(99),
                    gradient: LinearGradient(
                      colors: [visual.rules, visual.goldSoft, visual.empathy],
                    ),
                  ),
                ),
                if (value != null)
                  Positioned(
                    left: (constraints.maxWidth - markerSize) * normalized,
                    child: Container(
                      width: markerSize,
                      height: markerSize,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _countryValueColor(visual, value!),
                        border: Border.all(
                          color: visual.surfaceStrong,
                          width: 2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: _countryValueColor(
                              visual,
                              value!,
                            ).withValues(alpha: 0.28),
                            blurRadius: 8,
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}

final _atlasMarkers = <AtlasGlobeMarker>[
  for (final item in AtlasPreviewFixture.countries)
    AtlasGlobeMarker(
      countryCode: item.countryCode,
      value: item.value,
      normalizedPosition: Offset(item.markerX, item.markerY),
    ),
];

Color _countryValueColor(KefeVisualTheme visual, double value) {
  final normalized = (value / 10).clamp(0.0, 1.0);
  if (normalized <= 0.5) {
    return Color.lerp(visual.rules, visual.goldSoft, normalized * 2)!;
  }
  return Color.lerp(visual.goldSoft, visual.empathy, (normalized - 0.5) * 2)!;
}
