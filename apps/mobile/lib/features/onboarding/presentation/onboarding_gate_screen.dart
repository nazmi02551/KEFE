import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/application/decision_controller.dart';
import '../application/onboarding_controller.dart';

class OnboardingGateScreen extends ConsumerStatefulWidget {
  const OnboardingGateScreen({this.reviewMode = false, super.key});

  final bool reviewMode;

  @override
  ConsumerState<OnboardingGateScreen> createState() =>
      _OnboardingGateScreenState();
}

class _OnboardingGateScreenState extends ConsumerState<OnboardingGateScreen> {
  final _pageController = PageController();
  bool _ready = false;
  int _page = 0;

  @override
  void initState() {
    super.initState();
    Future.microtask(_resolveState);
  }

  Future<void> _resolveState() async {
    if (widget.reviewMode) {
      if (!mounted) return;
      setState(() => _ready = true);
      return;
    }

    final completed = await ref
        .read(onboardingControllerProvider)
        .isCompleted();
    if (!mounted) return;
    if (completed) {
      context.go('/explore');
      return;
    }
    setState(() => _ready = true);
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

    if (!_ready) {
      return Scaffold(
        backgroundColor: visual.canvas,
        body: SafeArea(
          child: Center(
            child: Semantics(
              liveRegion: true,
              label: strings.loading,
              child: KefeSurface(
                tone: KefeSurfaceTone.raised,
                accent: visual.rules,
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 16,
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.hourglass_empty_rounded, color: visual.rules),
                    const SizedBox(width: 12),
                    Text(
                      strings.loading,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: visual.mutedForeground,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

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
                children: [
                  _PromisePage(
                    key: const ValueKey('onboarding-promise-1'),
                    eyebrow: strings.appName,
                    title: strings.onboardingTitleOne,
                    body: strings.onboardingBodyOne,
                    icon: Icons.balance_rounded,
                    accent: visual.goldSoft,
                  ),
                  _PromisePage(
                    key: const ValueKey('onboarding-promise-2'),
                    eyebrow: strings.onboardingStepTwoEyebrow,
                    title: strings.onboardingTitleTwo,
                    body: strings.onboardingBodyTwo,
                    icon: Icons.shield_outlined,
                    accent: visual.rules,
                  ),
                ],
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
                    _PageProgress(page: _page),
                    const SizedBox(height: 14),
                    FilledButton.icon(
                      key: const ValueKey('onboarding-primary-button'),
                      onPressed: _page == 0
                          ? () => _pageController.nextPage(
                              duration: KefeMotion.resolve(
                                context,
                                const Duration(milliseconds: 220),
                              ),
                              curve: Curves.easeOut,
                            )
                          : () => context.go('/case/$demoCaseId?firstUse=1'),
                      icon: Icon(
                        _page == 0
                            ? Icons.arrow_forward_rounded
                            : Icons.balance_rounded,
                      ),
                      label: Text(
                        _page == 0
                            ? strings.onboardingNext
                            : strings.onboardingTryCase,
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

class _PromisePage extends StatelessWidget {
  const _PromisePage({
    required this.eyebrow,
    required this.title,
    required this.body,
    required this.icon,
    required this.accent,
    super.key,
  });

  final String eyebrow;
  final String title;
  final String body;
  final IconData icon;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    const padding = EdgeInsets.fromLTRB(20, 18, 20, 12);
    final visual = context.kefeVisual;
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        padding: padding,
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: math.max(0, constraints.maxHeight - padding.vertical),
          ),
          child: Center(
            child: KefeSurface(
              tone: KefeSurfaceTone.premium,
              accent: accent,
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
                          color: accent.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(
                            color: accent.withValues(alpha: 0.34),
                          ),
                        ),
                        child: ExcludeSemantics(
                          child: Icon(icon, color: accent, size: 29),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: KefeEyebrow(
                          eyebrow,
                          color: accent,
                          icon: Icons.circle,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 28),
                  Text(
                    title,
                    style: Theme.of(context).textTheme.displaySmall?.copyWith(
                      color: visual.onSurfaceStrong,
                      fontWeight: FontWeight.w900,
                      height: 1.08,
                      letterSpacing: -0.7,
                    ),
                  ),
                  const SizedBox(height: 18),
                  Text(
                    body,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: visual.onSurfaceStrong.withValues(alpha: 0.78),
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 30),
                  const _BalanceMotif(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _BalanceMotif extends StatelessWidget {
  const _BalanceMotif();

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return ExcludeSemantics(
      child: KefeSurface(
        tone: KefeSurfaceTone.sunken,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        borderRadius: 18,
        semanticContainer: false,
        child: Row(
          children: [
            _BalanceNode(icon: Icons.gavel_rounded, color: visual.rules),
            Expanded(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    height: 2,
                    margin: const EdgeInsets.symmetric(horizontal: 10),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [visual.rules, visual.goldSoft, visual.empathy],
                      ),
                      borderRadius: BorderRadius.circular(99),
                    ),
                  ),
                  Container(
                    width: 30,
                    height: 30,
                    decoration: BoxDecoration(
                      color: visual.surfaceStrong,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: visual.goldSoft.withValues(alpha: 0.55),
                      ),
                    ),
                    child: Icon(
                      Icons.balance_rounded,
                      color: visual.goldSoft,
                      size: 17,
                    ),
                  ),
                ],
              ),
            ),
            _BalanceNode(icon: Icons.favorite_rounded, color: visual.empathy),
          ],
        ),
      ),
    );
  }
}

class _BalanceNode extends StatelessWidget {
  const _BalanceNode({required this.icon, required this.color});

  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 38,
      height: 38,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.13),
        shape: BoxShape.circle,
        border: Border.all(color: color.withValues(alpha: 0.28)),
      ),
      child: Icon(icon, color: color, size: 19),
    );
  }
}

class _PageProgress extends StatelessWidget {
  const _PageProgress({required this.page});

  final int page;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Row(
      children: [
        for (var index = 0; index < 2; index++) ...[
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
          if (index == 0) const SizedBox(width: 8),
        ],
      ],
    );
  }
}
