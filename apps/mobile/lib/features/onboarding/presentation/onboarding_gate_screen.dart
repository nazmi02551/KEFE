import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/kefe_strings.dart';
import '../../decision/application/decision_controller.dart';
import '../application/onboarding_controller.dart';

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
                  ),
                  _PromisePage(
                    key: const ValueKey('onboarding-promise-2'),
                    eyebrow: strings.onboardingStepTwoEyebrow,
                    title: strings.onboardingTitleTwo,
                    body: strings.onboardingBodyTwo,
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(
                      2,
                      (index) => Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 180),
                          width: index == _page ? 24 : 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: index == _page
                                ? Theme.of(context).colorScheme.primary
                                : Theme.of(context).colorScheme.outlineVariant,
                            borderRadius: BorderRadius.circular(99),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  FilledButton(
                    key: const ValueKey('onboarding-primary-button'),
                    onPressed: _page == 0
                        ? () => _pageController.nextPage(
                            duration: const Duration(milliseconds: 220),
                            curve: Curves.easeOut,
                          )
                        : () => context.go('/case/$demoCaseId?firstUse=1'),
                    child: Text(
                      _page == 0
                          ? strings.onboardingNext
                          : strings.onboardingTryCase,
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
}

class _PromisePage extends StatelessWidget {
  const _PromisePage({
    required this.eyebrow,
    required this.title,
    required this.body,
    super.key,
  });

  final String eyebrow;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    const padding = EdgeInsets.all(28);
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        padding: padding,
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: math.max(
              0,
              constraints.maxHeight - padding.vertical,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                eyebrow,
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const SizedBox(height: 16),
              Text(title, style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 20),
              Text(body, style: Theme.of(context).textTheme.bodyLarge),
            ],
          ),
        ),
      ),
    );
  }
}
