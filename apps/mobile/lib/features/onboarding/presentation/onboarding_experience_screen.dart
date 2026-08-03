import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/experience_presentation_config.dart';
import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/application/decision_controller.dart';
import '../application/onboarding_controller.dart';
import 'onboarding_gate_screen.dart';
import 'onboarding_v2_strings.dart';

class OnboardingExperienceScreen extends ConsumerWidget {
  const OnboardingExperienceScreen({this.reviewMode = false, super.key});

  final bool reviewMode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final experience = ref.watch(experiencePresentationConfigProvider);
    if (experience.onboardingVersion == OnboardingExperienceVersion.legacyV1) {
      return OnboardingGateScreen(reviewMode: reviewMode);
    }
    return _ProgressiveOnboardingScreen(reviewMode: reviewMode);
  }
}

enum _ResolutionState { resolving, ready, error }

class _ProgressiveOnboardingScreen extends ConsumerStatefulWidget {
  const _ProgressiveOnboardingScreen({required this.reviewMode});

  final bool reviewMode;

  @override
  ConsumerState<_ProgressiveOnboardingScreen> createState() =>
      _ProgressiveOnboardingScreenState();
}

class _ProgressiveOnboardingScreenState
    extends ConsumerState<_ProgressiveOnboardingScreen> {
  final _pageController = PageController();
  _ResolutionState _resolution = _ResolutionState.resolving;
  bool _resolutionInFlight = false;
  int _page = 0;

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(_resolveState);
  }

  Future<void> _resolveState() async {
    if (_resolutionInFlight) return;
    if (widget.reviewMode) {
      if (mounted) setState(() => _resolution = _ResolutionState.ready);
      return;
    }

    _resolutionInFlight = true;
    if (mounted && _resolution != _ResolutionState.resolving) {
      setState(() => _resolution = _ResolutionState.resolving);
    }
    try {
      final completed = await ref
          .read(onboardingControllerProvider)
          .isCompleted();
      if (!mounted) return;
      if (completed) {
        context.go('/explore');
        return;
      }
      setState(() => _resolution = _ResolutionState.ready);
    } on Object {
      if (!mounted) return;
      setState(() => _resolution = _ResolutionState.error);
    } finally {
      _resolutionInFlight = false;
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    if (_resolution != _ResolutionState.ready) {
      final isError = _resolution == _ResolutionState.error;
      return Scaffold(
        backgroundColor: visual.canvas,
        body: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: KefeSurface(
                key: ValueKey(
                  isError ? 'onboarding-v2-error' : 'onboarding-v2-loading',
                ),
                tone: KefeSurfaceTone.raised,
                accent: isError ? visual.attention : visual.rules,
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 16,
                ),
                child: Semantics(
                  liveRegion: true,
                  label: isError ? strings.genericError : strings.loading,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            isError
                                ? Icons.cloud_off_outlined
                                : Icons.hourglass_empty_rounded,
                            color: isError ? visual.attention : visual.rules,
                          ),
                          const SizedBox(width: 12),
                          Flexible(
                            child: Text(
                              isError ? strings.genericError : strings.loading,
                              style: Theme.of(context).textTheme.bodyMedium
                                  ?.copyWith(
                                    color: visual.mutedForeground,
                                    fontWeight: FontWeight.w700,
                                    height: 1.4,
                                  ),
                            ),
                          ),
                        ],
                      ),
                      if (isError) ...[
                        const SizedBox(height: 14),
                        OutlinedButton(
                          key: const ValueKey('onboarding-v2-retry'),
                          onPressed: _resolveState,
                          child: Text(strings.retry),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      );
    }

    final pages = [
      _OnboardingPageData(
        key: const ValueKey('onboarding-promise-1'),
        eyebrow: strings.onboardingV2PageOneEyebrow,
        title: strings.onboardingV2PageOneTitle,
        body: strings.onboardingV2PageOneBody,
        icon: Icons.balance_rounded,
        accent: visual.goldSoft,
        motif: _OwnDecisionMotif(visual: visual),
      ),
      _OnboardingPageData(
        key: const ValueKey('onboarding-promise-2'),
        eyebrow: strings.onboardingV2PageTwoEyebrow,
        title: strings.onboardingV2PageTwoTitle,
        body: strings.onboardingV2PageTwoBody,
        icon: Icons.groups_2_outlined,
        accent: visual.rules,
        motif: _DistributionMotif(visual: visual),
      ),
      _OnboardingPageData(
        key: const ValueKey('onboarding-promise-3'),
        eyebrow: strings.onboardingV2PageThreeEyebrow,
        title: strings.onboardingV2PageThreeTitle,
        body: strings.onboardingV2PageThreeBody,
        icon: Icons.route_rounded,
        accent: visual.empathy,
        motif: _JourneyMotif(visual: visual),
      ),
    ];
    final lastPage = _page == pages.length - 1;

    return Scaffold(
      backgroundColor: visual.canvas,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView(
                key: const ValueKey('onboarding-pages'),
                controller: _pageController,
                onPageChanged: (page) => setState(() => _page = page),
                children: [for (final page in pages) _PromisePage(data: page)],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 22),
              child: KefeSurface(
                tone: KefeSurfaceTone.raised,
                padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
                borderRadius: 20,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _PageProgress(page: _page, count: pages.length),
                    const SizedBox(height: 14),
                    FilledButton.icon(
                      key: const ValueKey('onboarding-primary-button'),
                      onPressed: lastPage
                          ? () => context.go('/case/$demoCaseId?firstUse=1')
                          : () => _pageController.nextPage(
                              duration: KefeMotion.resolve(
                                context,
                                const Duration(milliseconds: 220),
                              ),
                              curve: Curves.easeOut,
                            ),
                      icon: Icon(
                        lastPage
                            ? Icons.balance_rounded
                            : Icons.arrow_forward_rounded,
                      ),
                      label: Text(
                        lastPage
                            ? strings.onboardingV2Start
                            : strings.onboardingV2Continue,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OnboardingPageData {
  const _OnboardingPageData({
    required this.key,
    required this.eyebrow,
    required this.title,
    required this.body,
    required this.icon,
    required this.accent,
    required this.motif,
  });

  final Key key;
  final String eyebrow;
  final String title;
  final String body;
  final IconData icon;
  final Color accent;
  final Widget motif;
}

class _PromisePage extends StatelessWidget {
  const _PromisePage({required this.data});

  final _OnboardingPageData data;

  @override
  Widget build(BuildContext context) {
    const padding = EdgeInsets.fromLTRB(20, 18, 20, 12);
    final visual = context.kefeVisual;
    return LayoutBuilder(
      key: data.key,
      builder: (context, constraints) => SingleChildScrollView(
        padding: padding,
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: math.max(0, constraints.maxHeight - padding.vertical),
          ),
          child: Center(
            child: KefeSurface(
              tone: KefeSurfaceTone.premium,
              accent: data.accent,
              padding: const EdgeInsets.all(24),
              borderRadius: 28,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 54,
                        height: 54,
                        decoration: BoxDecoration(
                          color: data.accent.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(
                            color: data.accent.withValues(alpha: 0.34),
                          ),
                        ),
                        child: ExcludeSemantics(
                          child: Icon(data.icon, color: data.accent, size: 29),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: KefeEyebrow(
                          data.eyebrow,
                          color: data.accent,
                          icon: Icons.circle,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 28),
                  Text(
                    data.title,
                    style: Theme.of(context).textTheme.displaySmall?.copyWith(
                      color: visual.onSurfaceStrong,
                      fontWeight: FontWeight.w900,
                      height: 1.08,
                      letterSpacing: -0.7,
                    ),
                  ),
                  const SizedBox(height: 18),
                  Text(
                    data.body,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: visual.onSurfaceStrong.withValues(alpha: 0.78),
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 30),
                  data.motif,
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _OwnDecisionMotif extends StatelessWidget {
  const _OwnDecisionMotif({required this.visual});

  final KefeVisualTheme visual;

  @override
  Widget build(BuildContext context) {
    return _MotifSurface(
      children: [
        _MotifNode(icon: Icons.gavel_rounded, color: visual.rules),
        Expanded(
          child: Stack(
            alignment: Alignment.center,
            children: [
              Container(height: 2, color: visual.goldSoft),
              _MotifNode(icon: Icons.lock_rounded, color: visual.goldSoft),
            ],
          ),
        ),
        _MotifNode(icon: Icons.favorite_rounded, color: visual.empathy),
      ],
    );
  }
}

class _DistributionMotif extends StatelessWidget {
  const _DistributionMotif({required this.visual});

  final KefeVisualTheme visual;

  @override
  Widget build(BuildContext context) {
    return _MotifSurface(
      children: [
        for (final height in [24.0, 38.0, 54.0, 34.0, 18.0]) ...[
          Expanded(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Container(
                height: height,
                decoration: BoxDecoration(
                  color: visual.rules.withValues(alpha: 0.72),
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
          const SizedBox(width: 7),
        ],
        _MotifNode(icon: Icons.my_location_rounded, color: visual.goldSoft),
      ],
    );
  }
}

class _JourneyMotif extends StatelessWidget {
  const _JourneyMotif({required this.visual});

  final KefeVisualTheme visual;

  @override
  Widget build(BuildContext context) {
    return _MotifSurface(
      children: [
        _MotifNode(icon: Icons.balance_rounded, color: visual.goldSoft),
        Expanded(
          child: Container(
            height: 2,
            margin: const EdgeInsets.symmetric(horizontal: 10),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [visual.goldSoft, visual.rules, visual.empathy],
              ),
            ),
          ),
        ),
        _MotifNode(icon: Icons.forum_outlined, color: visual.rules),
        Expanded(
          child: Container(
            height: 2,
            margin: const EdgeInsets.symmetric(horizontal: 10),
            color: visual.empathy,
          ),
        ),
        _MotifNode(icon: Icons.route_rounded, color: visual.empathy),
      ],
    );
  }
}

class _MotifSurface extends StatelessWidget {
  const _MotifSurface({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return ExcludeSemantics(
      child: KefeSurface(
        tone: KefeSurfaceTone.sunken,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        borderRadius: 18,
        semanticContainer: false,
        child: SizedBox(height: 60, child: Row(children: children)),
      ),
    );
  }
}

class _MotifNode extends StatelessWidget {
  const _MotifNode({required this.icon, required this.color});

  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.13),
        shape: BoxShape.circle,
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Icon(icon, color: color, size: 20),
    );
  }
}

class _PageProgress extends StatelessWidget {
  const _PageProgress({required this.page, required this.count});

  final int page;
  final int count;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      label: '${page + 1}/$count',
      child: Row(
        children: [
          for (var index = 0; index < count; index++) ...[
            Expanded(
              child: AnimatedContainer(
                duration: KefeMotion.resolve(
                  context,
                  const Duration(milliseconds: 180),
                ),
                height: 5,
                decoration: BoxDecoration(
                  color: index <= page ? visual.gold : visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(99),
                ),
              ),
            ),
            if (index < count - 1) const SizedBox(width: 8),
          ],
        ],
      ),
    );
  }
}
