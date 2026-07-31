import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/visual_composition/kefe_visual_composition_flutter.dart';
import '../../../core/visual_composition/kefe_visual_composition_models.dart';
import '../application/case_media_provider.dart';
import '../domain/case_media_models.dart';

class CaseMediaSurface extends ConsumerStatefulWidget {
  const CaseMediaSurface({
    required this.caseVersionId,
    required this.slot,
    this.postCommitAvailable = false,
    this.borderRadius = 20,
    super.key,
  });

  final String caseVersionId;
  final CaseMediaSlot slot;
  final bool postCommitAvailable;
  final double borderRadius;

  @override
  ConsumerState<CaseMediaSurface> createState() => _CaseMediaSurfaceState();
}

class _CaseMediaSurfaceState extends ConsumerState<CaseMediaSurface> {
  late Future<List<CaseMediaPresentation>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void didUpdateWidget(covariant CaseMediaSurface oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.caseVersionId != widget.caseVersionId ||
        oldWidget.slot != widget.slot ||
        oldWidget.postCommitAvailable != widget.postCommitAvailable) {
      _future = _load();
    }
  }

  Future<List<CaseMediaPresentation>> _load() => ref
      .read(caseMediaRepositoryProvider)
      .fetchForCaseVersion(
        widget.caseVersionId,
        slot: widget.slot,
        postCommitAvailable: widget.postCommitAvailable,
      );

  double get _defaultAspectRatio => switch (widget.slot) {
    CaseMediaSlot.caseHero => 1.85,
    CaseMediaSlot.exploreCard || CaseMediaSlot.contextSupporting => 1.55,
  };

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<CaseMediaPresentation>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting &&
            !snapshot.hasData) {
          return KefeVisualCompositionPlaceholder(
            placeholderKey: ValueKey(
              'case-media-loading-${widget.slot.code}-${widget.caseVersionId}',
            ),
            aspectRatio: _defaultAspectRatio,
            borderRadius: widget.borderRadius,
            kind: KefeVisualPlaceholderKind.loading,
          );
        }

        if (snapshot.hasError) {
          return SizedBox.shrink(
            key: ValueKey(
              'case-media-error-${widget.slot.code}-${widget.caseVersionId}',
            ),
          );
        }

        final items = snapshot.data;
        if (items == null || items.isEmpty) {
          return SizedBox.shrink(
            key: ValueKey(
              'case-media-empty-${widget.slot.code}-${widget.caseVersionId}',
            ),
          );
        }

        final item = items.firstWhere(
          (candidate) =>
              candidate.exposurePhase == MediaExposurePhase.preCommitSafe ||
              widget.postCommitAvailable,
          orElse: () => items.first,
        );
        if (item.exposurePhase == MediaExposurePhase.postCommitOnly &&
            !widget.postCommitAvailable) {
          return SizedBox.shrink(
            key: ValueKey(
              'case-media-exposure-blocked-${item.slot.code}-${item.caseVersionId}',
            ),
          );
        }

        return _MediaRenderer(item: item, borderRadius: widget.borderRadius);
      },
    );
  }
}

class _MediaRenderer extends StatelessWidget {
  const _MediaRenderer({required this.item, required this.borderRadius});

  final CaseMediaPresentation item;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    final policy = item.rendition.composition;
    if (!policy.supportsBrightness(Theme.of(context).brightness)) {
      return _fallback(context, policy, 'theme');
    }
    if (item.rendition.rendererCode != 'KEFE_ABSTRACT_V1') {
      return _fallback(context, policy, 'renderer');
    }

    final visual = _visualFor(context, item.rendition.locator);
    final media = AspectRatio(
      aspectRatio: item.rendition.aspectRatio,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: DecoratedBox(
          key: ValueKey('case-media-${item.slot.code}-${item.caseVersionId}'),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: visual.colors,
            ),
          ),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final safePadding = policy.safePaddingFor(
                Size(constraints.maxWidth, constraints.maxHeight),
              );
              return Stack(
                fit: StackFit.expand,
                children: [
                  CustomPaint(
                    painter: _AbstractMediaPainter(
                      accent: visual.accent,
                      line: context.kefeVisual.goldSoft,
                    ),
                  ),
                  Align(
                    alignment: policy.focalAlignment,
                    child: Container(
                      width: 82,
                      height: 82,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: context.kefeVisual.surfaceStrong.withValues(
                          alpha: 0.76,
                        ),
                        border: Border.all(
                          color: context.kefeVisual.goldSoft.withValues(
                            alpha: 0.34,
                          ),
                        ),
                      ),
                      child: Icon(
                        visual.icon,
                        size: 40,
                        color: context.kefeVisual.goldSoft,
                      ),
                    ),
                  ),
                  if (item.attribution != null)
                    Align(
                      alignment: Alignment.bottomLeft,
                      child: Padding(
                        padding: safePadding,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 5,
                          ),
                          decoration: BoxDecoration(
                            color: context.kefeVisual.surfaceStrong.withValues(
                              alpha: 0.84,
                            ),
                            borderRadius: BorderRadius.circular(99),
                          ),
                          child: Text(
                            item.attribution!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.labelSmall
                                ?.copyWith(
                                  color: context.kefeVisual.onSurfaceStrong
                                      .withValues(alpha: 0.72),
                                  fontSize: 9,
                                ),
                          ),
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      ),
    );

    if (item.decorative) {
      return ExcludeSemantics(child: media);
    }
    return Semantics(image: true, label: item.altText, child: media);
  }

  Widget _fallback(
    BuildContext context,
    KefeVisualCompositionPolicy policy,
    String reason,
  ) {
    if (policy.fallback == KefeVisualFallbackPolicy.textHierarchyOnly) {
      return SizedBox.shrink(
        key: ValueKey(
          'case-media-fallback-$reason-${item.slot.code}-${item.caseVersionId}',
        ),
      );
    }
    return KefeVisualCompositionPlaceholder(
      placeholderKey: ValueKey(
        'case-media-fallback-$reason-${item.slot.code}-${item.caseVersionId}',
      ),
      aspectRatio: item.rendition.aspectRatio,
      borderRadius: borderRadius,
      kind: KefeVisualPlaceholderKind.unavailable,
      semanticLabel: item.decorative ? null : item.altText,
    );
  }
}

class _AbstractMediaPainter extends CustomPainter {
  const _AbstractMediaPainter({required this.accent, required this.line});

  final Color accent;
  final Color line;

  @override
  void paint(Canvas canvas, Size size) {
    final soft = Paint()
      ..color = accent.withValues(alpha: 0.13)
      ..style = PaintingStyle.fill;
    final linePaint = Paint()
      ..color = line.withValues(alpha: 0.22)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.4;

    canvas.drawCircle(Offset(size.width * 0.14, size.height * 0.22), 34, soft);
    canvas.drawCircle(Offset(size.width * 0.88, size.height * 0.72), 54, soft);
    canvas.drawCircle(Offset(size.width * 0.76, size.height * 0.16), 18, soft);

    final path = Path()
      ..moveTo(size.width * 0.05, size.height * 0.80)
      ..quadraticBezierTo(
        size.width * 0.32,
        size.height * 0.52,
        size.width * 0.51,
        size.height * 0.68,
      )
      ..quadraticBezierTo(
        size.width * 0.75,
        size.height * 0.90,
        size.width * 0.97,
        size.height * 0.46,
      );
    canvas.drawPath(path, linePaint);
  }

  @override
  bool shouldRepaint(covariant _AbstractMediaPainter oldDelegate) =>
      oldDelegate.accent != accent || oldDelegate.line != line;
}

({IconData icon, Color accent, List<Color> colors}) _visualFor(
  BuildContext context,
  String locator,
) {
  final visual = context.kefeVisual;
  Color blend(Color accent, double amount) =>
      Color.lerp(visual.surfaceStrong, accent, amount)!;

  return switch (locator) {
    'RESOURCE_PRIORITY' => (
      icon: Icons.airline_seat_recline_normal_rounded,
      accent: visual.empathy,
      colors: [
        blend(visual.rules, 0.32),
        visual.surfaceStrong,
        blend(visual.empathy, 0.30),
      ],
    ),
    'DATA_NETWORK' => (
      icon: Icons.hub_rounded,
      accent: visual.rules,
      colors: [
        blend(visual.rules, 0.38),
        visual.surfaceStrong,
        blend(visual.burgundy, 0.24),
      ],
    ),
    'SPORTS_DECISION' => (
      icon: Icons.sports_soccer_rounded,
      accent: visual.success,
      colors: [
        blend(visual.success, 0.30),
        visual.surfaceStrong,
        blend(visual.burgundy, 0.18),
      ],
    ),
    'CIVIC_TRANSPARENCY' => (
      icon: Icons.account_balance_outlined,
      accent: visual.gold,
      colors: [
        blend(visual.gold, 0.24),
        visual.surfaceStrong,
        blend(visual.rules, 0.22),
      ],
    ),
    'REMOTE_WORK' => (
      icon: Icons.laptop_mac_rounded,
      accent: visual.rules,
      colors: [
        blend(visual.rules, 0.30),
        visual.surfaceStrong,
        blend(visual.burgundy, 0.24),
      ],
    ),
    'AIR_TRAVEL' => (
      icon: Icons.airplanemode_active_rounded,
      accent: visual.gold,
      colors: [
        blend(visual.rules, 0.31),
        visual.surfaceStrong,
        blend(visual.empathy, 0.22),
      ],
    ),
    'WORK_TRANSITION' => (
      icon: Icons.model_training_rounded,
      accent: visual.attention,
      colors: [
        blend(visual.attention, 0.25),
        visual.surfaceStrong,
        blend(visual.rules, 0.21),
      ],
    ),
    'EDUCATION_AI' => (
      icon: Icons.school_rounded,
      accent: visual.empathy,
      colors: [
        blend(visual.burgundy, 0.25),
        visual.surfaceStrong,
        blend(visual.rules, 0.24),
      ],
    ),
    _ => (
      icon: Icons.image_outlined,
      accent: visual.gold,
      colors: [
        blend(visual.rules, 0.25),
        visual.surfaceStrong,
        blend(visual.burgundy, 0.20),
      ],
    ),
  };
}
