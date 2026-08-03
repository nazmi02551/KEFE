import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/experience_presentation_config.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../decision/application/decision_controller.dart';
import '../application/onboarding_controller.dart';
import 'onboarding_v2_strings.dart';

class OnboardingGateScreen extends ConsumerStatefulWidget {
  const OnboardingGateScreen({super.key});

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
    final experience = ref.watch(experiencePresentationConfigProvider);
    final pages = experience.onboardingVersion == OnboardingExperienceVersion.v2
        ? _v2Pages(strings)
        : _legacyPages(strings);
    final currentPage = _page.clamp(0, pages.length - 1);
    final lastPage = currentPage == pages.length - 1;

    if (!_ready) {
      return Scaffold(
        body: SafeArea(
          child: Center(
            child: Semantics(
              label: strings.loading,
              child: const CircularProgressIndicator(),
            ),
          ),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                key: const ValueKey('onboarding-pages'),
                controller: _pageController,
                itemCount: pages.length,
                onPageChanged: (page) => setState(() => _page = page),
                itemBuilder: (context, index) {
                  final page = pages[index];
                  return _PromisePage(
                    key: ValueKey('onboarding-promise-${index + 1}'),
                    eyebrow: page.eyebrow,
                    title: page.title,
                    body: page.body,
                    icon: page.icon,
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Semantics(
                    label: '${currentPage + 1}/${pages.length}',
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(
                        pages.length,
                        (index) => Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 180),
                            width: index == currentPage ? 24 : 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: index == currentPage
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).colorScheme.outlineVariant,
                              borderRadius: BorderRadius.circular(99),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  FilledButton(
                    key: const ValueKey('onboarding-primary-button'),
                    onPressed: lastPage
                        ? () => context.go('/case/$demoCaseId?firstUse=1')
                        : () => _pageController.nextPage(
                            duration: const Duration(milliseconds: 220),
                            curve: Curves.easeOut,
                          ),
                    child: Text(
                      experience.onboardingVersion == OnboardingExperienceVersion.v2
                          ? lastPage
                                ? strings.onboardingV2Start
                                : strings.onboardingV2Continue
                          : lastPage
                          ? strings.onboardingTryCase
                          : strings.onboardingNext,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<_OnboardingPageData> _v2Pages(KefeStrings strings) => [
        _OnboardingPageData(
          eyebrow: strings.onboardingV2PageOneEyebrow,
          title: strings.onboardingV2PageOneTitle,
          body: strings.onboardingV2PageOneBody,
          icon: Icons.balance_rounded,
        ),
        _OnboardingPageData(
          eyebrow: strings.onboardingV2PageTwoEyebrow,
          title: strings.onboardingV2PageTwoTitle,
          body: strings.onboardingV2PageTwoBody,
          icon: Icons.groups_2_outlined,
        ),
        _OnboardingPageData(
          eyebrow: strings.onboardingV2PageThreeEyebrow,
          title: strings.onboardingV2PageThreeTitle,
          body: strings.onboardingV2PageThreeBody,
          icon: Icons.route_rounded,
        ),
      ];

  List<_OnboardingPageData> _legacyPages(KefeStrings strings) => [
        _OnboardingPageData(
          eyebrow: strings.appName,
          title: strings.onboardingTitleOne,
          body: strings.onboardingBodyOne,
          icon: Icons.balance_rounded,
        ),
        _OnboardingPageData(
          eyebrow: strings.onboardingStepTwoEyebrow,
          title: strings.onboardingTitleTwo,
          body: strings.onboardingBodyTwo,
          icon: Icons.compare_arrows_rounded,
        ),
      ];
}

class _PromisePage extends StatelessWidget {
  const _PromisePage({
    required this.eyebrow,
    required this.title,
    required this.body,
    required this.icon,
    super.key,
  });

  final String eyebrow;
  final String title;
  final String body;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    const padding = EdgeInsets.all(28);
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        padding: padding,
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: math.max(0, constraints.maxHeight - padding.vertical),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Icon(
                  icon,
                  size: 29,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
              const SizedBox(height: 24),
              Text(
                eyebrow,
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  color: Theme.of(context).colorScheme.primary,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 16),
              Text(title, style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 20),
              Text(
                body,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OnboardingPageData {
  const _OnboardingPageData({
    required this.eyebrow,
    required this.title,
    required this.body,
    required this.icon,
  });

  final String eyebrow;
  final String title;
  final String body;
  final IconData icon;
}
