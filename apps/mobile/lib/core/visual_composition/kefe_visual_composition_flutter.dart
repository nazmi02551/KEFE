import 'package:flutter/material.dart';

import '../design/kefe_visual_system.dart';
import 'kefe_visual_composition_models.dart';

enum KefeVisualPlaceholderKind { loading, unavailable }

extension KefeVisualCompositionFlutter on KefeVisualCompositionPolicy {
  BoxFit get boxFit => switch (fit) {
    KefeVisualFitPolicy.cover => BoxFit.cover,
    KefeVisualFitPolicy.contain => BoxFit.contain,
  };

  Alignment get focalAlignment =>
      Alignment((focalPoint.x * 2) - 1, (focalPoint.y * 2) - 1);

  bool supportsBrightness(Brightness brightness) => switch (themeSuitability) {
    KefeVisualThemeSuitability.adaptive => true,
    KefeVisualThemeSuitability.lightOnly => brightness == Brightness.light,
    KefeVisualThemeSuitability.darkOnly => brightness == Brightness.dark,
  };

  EdgeInsets safePaddingFor(Size size) => EdgeInsets.fromLTRB(
    size.width * safeArea.left,
    size.height * safeArea.top,
    size.width * safeArea.right,
    size.height * safeArea.bottom,
  );
}

class KefeVisualCompositionPlaceholder extends StatelessWidget {
  const KefeVisualCompositionPlaceholder({
    required this.aspectRatio,
    required this.borderRadius,
    required this.kind,
    this.semanticLabel,
    this.placeholderKey,
    super.key,
  });

  final double aspectRatio;
  final double borderRadius;
  final KefeVisualPlaceholderKind kind;
  final String? semanticLabel;
  final Key? placeholderKey;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final icon = switch (kind) {
      KefeVisualPlaceholderKind.loading => Icons.hourglass_top_rounded,
      KefeVisualPlaceholderKind.unavailable =>
        Icons.image_not_supported_outlined,
    };
    final body = AspectRatio(
      aspectRatio: aspectRatio,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: DecoratedBox(
          key: placeholderKey,
          decoration: BoxDecoration(
            color: visual.surfaceSunken,
            border: Border.all(color: visual.border),
          ),
          child: Center(
            child: Icon(
              icon,
              size: 28,
              color: visual.mutedForeground.withValues(alpha: 0.62),
            ),
          ),
        ),
      ),
    );

    final label = semanticLabel;
    if (label == null || label.isEmpty) {
      return ExcludeSemantics(child: body);
    }
    return Semantics(image: true, label: label, child: body);
  }
}
