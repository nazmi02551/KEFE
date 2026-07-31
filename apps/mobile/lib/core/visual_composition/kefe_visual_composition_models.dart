enum KefeVisualFitPolicy { cover, contain }

enum KefeVisualThemeSuitability { adaptive, lightOnly, darkOnly }

enum KefeVisualFallbackPolicy { textHierarchyOnly, semanticPlaceholder }

enum KefeVisualMotionPolicy { staticOnly, reducedMotionAware }

enum KefeVisualCacheClass { compact, hero }

class KefeVisualFocalPoint {
  const KefeVisualFocalPoint({this.x = 0.5, this.y = 0.5})
    : assert(x >= 0 && x <= 1),
      assert(y >= 0 && y <= 1);

  final double x;
  final double y;
}

class KefeVisualSafeArea {
  const KefeVisualSafeArea({
    this.left = 0,
    this.top = 0,
    this.right = 0,
    this.bottom = 0,
  }) : assert(left >= 0 && left <= 0.25),
       assert(top >= 0 && top <= 0.25),
       assert(right >= 0 && right <= 0.25),
       assert(bottom >= 0 && bottom <= 0.25);

  final double left;
  final double top;
  final double right;
  final double bottom;

  static const none = KefeVisualSafeArea();
  static const card = KefeVisualSafeArea(
    left: 0.045,
    top: 0.045,
    right: 0.045,
    bottom: 0.045,
  );
  static const hero = KefeVisualSafeArea(
    left: 0.055,
    top: 0.055,
    right: 0.055,
    bottom: 0.055,
  );
}

class KefeVisualPerformanceBudget {
  const KefeVisualPerformanceBudget({
    required this.maxDecodeWidthPx,
    required this.maxDecodeHeightPx,
    required this.maxDecodedBytes,
    required this.cacheClass,
  }) : assert(maxDecodeWidthPx > 0),
       assert(maxDecodeHeightPx > 0),
       assert(maxDecodedBytes > 0);

  final int maxDecodeWidthPx;
  final int maxDecodeHeightPx;
  final int maxDecodedBytes;
  final KefeVisualCacheClass cacheClass;

  static const compact = KefeVisualPerformanceBudget(
    maxDecodeWidthPx: 960,
    maxDecodeHeightPx: 960,
    maxDecodedBytes: 4 * 1024 * 1024,
    cacheClass: KefeVisualCacheClass.compact,
  );

  static const hero = KefeVisualPerformanceBudget(
    maxDecodeWidthPx: 1600,
    maxDecodeHeightPx: 1200,
    maxDecodedBytes: 8 * 1024 * 1024,
    cacheClass: KefeVisualCacheClass.hero,
  );
}

class KefeVisualCompositionPolicy {
  const KefeVisualCompositionPolicy({
    this.fit = KefeVisualFitPolicy.cover,
    this.focalPoint = const KefeVisualFocalPoint(),
    this.safeArea = KefeVisualSafeArea.none,
    this.themeSuitability = KefeVisualThemeSuitability.adaptive,
    this.fallback = KefeVisualFallbackPolicy.textHierarchyOnly,
    this.motion = KefeVisualMotionPolicy.staticOnly,
    this.performance = KefeVisualPerformanceBudget.compact,
  });

  final KefeVisualFitPolicy fit;
  final KefeVisualFocalPoint focalPoint;
  final KefeVisualSafeArea safeArea;
  final KefeVisualThemeSuitability themeSuitability;
  final KefeVisualFallbackPolicy fallback;
  final KefeVisualMotionPolicy motion;
  final KefeVisualPerformanceBudget performance;

  static const card = KefeVisualCompositionPolicy(
    safeArea: KefeVisualSafeArea.card,
    fallback: KefeVisualFallbackPolicy.textHierarchyOnly,
    motion: KefeVisualMotionPolicy.reducedMotionAware,
    performance: KefeVisualPerformanceBudget.compact,
  );

  static const hero = KefeVisualCompositionPolicy(
    safeArea: KefeVisualSafeArea.hero,
    fallback: KefeVisualFallbackPolicy.semanticPlaceholder,
    motion: KefeVisualMotionPolicy.reducedMotionAware,
    performance: KefeVisualPerformanceBudget.hero,
  );
}
