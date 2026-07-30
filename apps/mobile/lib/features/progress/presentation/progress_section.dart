import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/progress_controller.dart';
import 'progress_strings.dart';

class ProgressSection extends ConsumerStatefulWidget {
  const ProgressSection({super.key});

  @override
  ConsumerState<ProgressSection> createState() => _ProgressSectionState();
}

class _ProgressSectionState extends ConsumerState<ProgressSection> {
  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(progressControllerProvider.notifier).load(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final state = ref.watch(progressControllerProvider);

    return switch (state.uiState) {
      ProgressUiState.idle || ProgressUiState.loading => Card(
        key: const ValueKey('progress-loading'),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Semantics(
            liveRegion: true,
            label: strings.progressLoading,
            child: Text(strings.progressLoading),
          ),
        ),
      ),
      ProgressUiState.errorRetryable => Card(
        key: const ValueKey('progress-error'),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(strings.progressUnavailable),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: ref.read(progressControllerProvider.notifier).load,
                child: Text(strings.progressRetry),
              ),
            ],
          ),
        ),
      ),
      ProgressUiState.ready => _ProgressReady(state: state),
    };
  }
}

class _ProgressReady extends ConsumerWidget {
  const _ProgressReady({required this.state});

  final ProgressState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final envelope = state.envelope!;
    final progress = envelope.progress;
    final offer = envelope.accountOffer;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          key: const ValueKey('my-kefe-progress'),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  strings.progressTitle,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(strings.progressReadiness(progress.readiness)),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    _ProgressMetric(
                      label: strings.progressWeighs,
                      value: progress.meaningfulWeighCount,
                    ),
                    _ProgressMetric(
                      label: strings.progressCases,
                      value: progress.distinctCaseCount,
                    ),
                    _ProgressMetric(
                      label: strings.progressDomains,
                      value: progress.distinctDomainCount,
                    ),
                  ],
                ),
                if (progress.recentCases.isNotEmpty) ...[
                  const SizedBox(height: 18),
                  Text(
                    strings.progressRecent,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  for (final item in progress.recentCases)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Text('• ${item.title} · ${strings.domainName(item.primaryDomain)}'),
                    ),
                ],
                const SizedBox(height: 12),
                Text(
                  strings.progressMethodology,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ),
        if (offer.eligible && !state.offerDismissed) ...[
          const SizedBox(height: 12),
          Card(
            key: const ValueKey('account-offer'),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    strings.accountOfferTitle,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(strings.accountOfferBody),
                  const SizedBox(height: 12),
                  if (offer.accountCreationAvailable)
                    FilledButton.icon(
                      key: const ValueKey('account-offer-create'),
                      onPressed: () => context.push('/account'),
                      icon: const Icon(Icons.verified_user_outlined),
                      label: Text(strings.accountProtectAction),
                    )
                  else
                    Text(
                      strings.accountOfferUnavailable,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  const SizedBox(height: 8),
                  OutlinedButton(
                    key: const ValueKey('account-offer-continue-guest'),
                    onPressed: ref
                        .read(progressControllerProvider.notifier)
                        .dismissOffer,
                    child: Text(strings.continueAsGuest),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _ProgressMetric extends StatelessWidget {
  const _ProgressMetric({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label: $value',
      child: Container(
        constraints: const BoxConstraints(minWidth: 92),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(
            color: Theme.of(context).colorScheme.outlineVariant,
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Text('$value', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
