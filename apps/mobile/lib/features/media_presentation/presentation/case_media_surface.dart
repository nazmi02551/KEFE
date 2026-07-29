import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_theme.dart';
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

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<CaseMediaPresentation>>(
      future: _future,
      builder: (context, snapshot) {
        final items = snapshot.data;
        if (items == null || items.isEmpty) {
          return const SizedBox.shrink();
        }

        final item = items.firstWhere(
          (candidate) =>
              candidate.exposurePhase == MediaExposurePhase.preCommitSafe ||
              widget.postCommitAvailable,
          orElse: () => items.first,
        );
        if (item.exposurePhase == MediaExposurePhase.postCommitOnly &&
            !widget.postCommitAvailable) {
          return const SizedBox.shrink();
        }

        return _MediaRenderer(
          item: item,
          borderRadius: widget.borderRadius,
        );
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
    if (item.rendition.rendererCode != 'KEFE_ABSTRACT_V1') {
      return const SizedBox.shrink();
    }

    final visual = _visualFor(item.rendition.locator);
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
          child: Stack(
            fit: StackFit.expand,
            children: [
              CustomPaint(
                painter: _AbstractMediaPainter(accent: visual.accent),
              ),
              Align(
                alignment: Alignment.center,
                child: Container(
                  width: 82,
                  height: 82,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF07111F).withValues(alpha: 0.54),
                    border: Border.all(
                      color: KefeColorTokens.goldSoft.withValues(alpha: 0.32),
                    ),
                  ),
                  child: Icon(
                    visual.icon,
                    size: 40,
                    color: KefeColorTokens.goldSoft,
                  ),
                ),
              ),
              if (item.attribution != null)
                Align(
                  alignment: Alignment.bottomLeft,
                  child: Padding(
                    padding: const EdgeInsets.all(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 5,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFF07111F).withValues(alpha: 0.72),
                        borderRadius: BorderRadius.circular(99),
                      ),
                      child: Text(
                        item.attribution!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: KefeColorTokens.textMutedDark,
                              fontSize: 9,
                            ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );

    if (item.decorative) {
      return ExcludeSemantics(child: media);
    }
    return Semantics(
      image: true,
      label: item.altText,
      child: media,
    );
  }
}

class _AbstractMediaPainter extends CustomPainter {
  const _AbstractMediaPainter({required this.accent});

  final Color accent;

  @override
  void paint(Canvas canvas, Size size) {
    final soft = Paint()
      ..color = accent.withValues(alpha: 0.13)
      ..style = PaintingStyle.fill;
    final line = Paint()
      ..color = KefeColorTokens.goldSoft.withValues(alpha: 0.22)
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
    canvas.drawPath(path, line);
  }

  @override
  bool shouldRepaint(covariant _AbstractMediaPainter oldDelegate) =>
      oldDelegate.accent != accent;
}

({IconData icon, Color accent, List<Color> colors}) _visualFor(
  String locator,
) {
  return switch (locator) {
    'RESOURCE_PRIORITY' => (
        icon: Icons.airline_seat_recline_normal_rounded,
        accent: KefeColorTokens.empathy,
        colors: const [Color(0xFF162C49), Color(0xFF241C38), Color(0xFF3A2027)],
      ),
    'DATA_NETWORK' => (
        icon: Icons.hub_rounded,
        accent: KefeColorTokens.rules,
        colors: const [Color(0xFF102D4D), Color(0xFF18243A), Color(0xFF28223B)],
      ),
    'SPORTS_DECISION' => (
        icon: Icons.sports_soccer_rounded,
        accent: KefeColorTokens.success,
        colors: const [Color(0xFF123B34), Color(0xFF172A38), Color(0xFF241D30)],
      ),
    'CIVIC_TRANSPARENCY' => (
        icon: Icons.account_balance_outlined,
        accent: KefeColorTokens.gold,
        colors: const [Color(0xFF30311E), Color(0xFF172B3C), Color(0xFF251C2D)],
      ),
    'REMOTE_WORK' => (
        icon: Icons.laptop_mac_rounded,
        accent: KefeColorTokens.rules,
        colors: const [Color(0xFF15324B), Color(0xFF19243A), Color(0xFF312235)],
      ),
    'AIR_TRAVEL' => (
        icon: Icons.airplanemode_active_rounded,
        accent: KefeColorTokens.gold,
        colors: const [Color(0xFF173A5B), Color(0xFF17233A), Color(0xFF3A242A)],
      ),
    'WORK_TRANSITION' => (
        icon: Icons.model_training_rounded,
        accent: KefeColorTokens.attention,
        colors: const [Color(0xFF34301E), Color(0xFF20283A), Color(0xFF38222C)],
      ),
    'EDUCATION_AI' => (
        icon: Icons.school_rounded,
        accent: KefeColorTokens.empathy,
        colors: const [Color(0xFF232A51), Color(0xFF16263C), Color(0xFF3A202D)],
      ),
    _ => (
        icon: Icons.image_outlined,
        accent: KefeColorTokens.gold,
        colors: const [Color(0xFF14273C), Color(0xFF171C2A), Color(0xFF2B2029)],
      ),
  };
}
