import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/design/kefe_surface.dart';
import '../../core/design/kefe_visual_system.dart';
import '../../core/localization/kefe_content_localizer.dart';
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
          ),
          const SizedBox(height: 24),
          Text(
            strings.countryAverages,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 12),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 1.18,
              crossAxisSpacing: 11,
              mainAxisSpacing: 11,
            ),
            itemCount: AtlasPreviewFixture.countries.length,
            itemBuilder: (context, index) {
              final item = AtlasPreviewFixture.countries[index];
              return _CountryAverageCard(
                country: strings.country(item.countryCode),
                value: item.value,
                averageLabel: strings.average,
              );
            },
          ),
        ],
      ),
    );
  }
}

class _AtlasHero extends StatelessWidget {
  const _AtlasHero({required this.selectedCaseTitle, required this.strings});

  final String selectedCaseTitle;
  final AtlasPreviewStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('atlas-hero'),
      tone: KefeSurfaceTone.premium,
      accent: visual.gold,
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: visual.gold.withValues(alpha: 0.13),
                  borderRadius: BorderRadius.circular(13),
                  border: Border.all(
                    color: visual.gold.withValues(alpha: 0.24),
                  ),
                ),
                child: Icon(Icons.public_rounded, color: visual.goldSoft),
              ),
              const SizedBox(width: 12),
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
          ),
          const SizedBox(height: 16),
          Text(
            strings.worldView,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: visual.goldSoft,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.4,
            ),
          ),
          const SizedBox(height: 8),
          ExcludeSemantics(
            child: SizedBox(
              height: 190,
              child: CustomPaint(
                painter: _AtlasWorldPainter(visual),
                child: Center(
                  child: Container(
                    width: 126,
                    height: 126,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: visual.rules.withValues(alpha: 0.07),
                      border: Border.all(
                        color: visual.rules.withValues(alpha: 0.22),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: visual.rules.withValues(alpha: 0.10),
                          blurRadius: 34,
                          spreadRadius: 5,
                        ),
                      ],
                    ),
                    child: Icon(
                      Icons.public_rounded,
                      size: 78,
                      color: visual.rules.withValues(alpha: 0.76),
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          _AtlasContinuum(strings: strings),
        ],
      ),
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
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            Expanded(
              child: Text(
                strings.empathyCompassion,
                textAlign: TextAlign.end,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: visual.goldSoft,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 7),
        _ScaleTrack(value: null),
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
    required this.country,
    required this.value,
    required this.averageLabel,
  });

  final String country;
  final double value;
  final String averageLabel;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final formattedValue = value.toStringAsFixed(1);
    return Semantics(
      container: true,
      label: '$country · $averageLabel $formattedValue / 10',
      child: KefeSurface(
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(15),
        borderRadius: 18,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              country,
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              averageLabel,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.mutedForeground,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              formattedValue,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: visual.goldSoft,
                fontWeight: FontWeight.w900,
              ),
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
          final markerSize = 11.0;
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
                      colors: [visual.rules, visual.gold, visual.empathy],
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
                        color: visual.goldSoft,
                        border: Border.all(
                          color: visual.surfaceStrong,
                          width: 2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: visual.gold.withValues(alpha: 0.28),
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

class _AtlasWorldPainter extends CustomPainter {
  const _AtlasWorldPainter(this.visual);

  final KefeVisualTheme visual;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) * 0.40;
    final linePaint = Paint()
      ..color = visual.rules.withValues(alpha: 0.16)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    final orbitPaint = Paint()
      ..color = visual.gold.withValues(alpha: 0.12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;

    canvas.drawCircle(center, radius, linePaint);
    canvas.drawOval(
      Rect.fromCenter(
        center: center,
        width: radius * 2,
        height: radius * 0.72,
      ),
      linePaint,
    );
    canvas.drawOval(
      Rect.fromCenter(
        center: center,
        width: radius * 0.78,
        height: radius * 2,
      ),
      linePaint,
    );
    canvas.drawArc(
      Rect.fromCenter(
        center: center,
        width: radius * 2.7,
        height: radius * 1.30,
      ),
      -0.22,
      math.pi * 1.38,
      false,
      orbitPaint,
    );

    final dotPaint = Paint()..color = visual.goldSoft.withValues(alpha: 0.55);
    for (final offset in const [
      Offset(-0.55, -0.18),
      Offset(-0.18, 0.42),
      Offset(0.22, -0.47),
      Offset(0.58, 0.12),
      Offset(0.40, 0.50),
    ]) {
      canvas.drawCircle(
        center + Offset(offset.dx * radius, offset.dy * radius),
        2.2,
        dotPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _AtlasWorldPainter oldDelegate) =>
      oldDelegate.visual.rules != visual.rules ||
      oldDelegate.visual.gold != visual.gold ||
      oldDelegate.visual.isDark != visual.isDark;
}
