import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
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
      ProgressUiState.idle || ProgressUiState.loading => KefeSurface(
        key: const ValueKey('progress-loading'),
        child: Semantics(
          liveRegion: true,
          label: strings.progressLoading,
          child: Row(
            children: [
              const SizedBox.square(
                dimension: 18,
                child: Icon(Icons.hourglass_top_rounded, size: 18),
              ),
              const SizedBox(width: 12),
              Expanded(child: Text(strings.progressLoading)),
            ],
          ),
        ),
      ),
      ProgressUiState.errorRetryable => KefeSurface(
        key: const ValueKey('progress-error'),
        tone: KefeSurfaceTone.raised,
        accent: context.kefeVisual.attention,
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
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeSurface(
          key: const ValueKey('my-kefe-progress'),
          tone: KefeSurfaceTone.premium,
          accent: visual.gold,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              KefeEyebrow(strings.progressTitle, icon: Icons.insights_rounded),
              const SizedBox(height: 9),
              Text(
                strings.progressReadiness(progress.readiness),
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: visual.onSurfaceStrong.withValues(alpha: 0.82),
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _ProgressMetric(
                      label: strings.progressWeighs,
                      value: progress.meaningfulWeighCount,
                      accent: visual.goldSoft,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _ProgressMetric(
                      label: strings.progressCases,
                      value: progress.distinctCaseCount,
                      accent: visual.rules,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _ProgressMetric(
                      label: strings.progressDomains,
                      value: progress.distinctDomainCount,
                      accent: visual.empathy,
                    ),
                  ),
                ],
              ),
              if (progress.recentCases.isNotEmpty) ...[
                const SizedBox(height: 18),
                Text(
                  strings.progressRecent,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 9),
                for (final item in progress.recentCases)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 7,
                          height: 7,
                          margin: const EdgeInsets.only(top: 6),
                          decoration: BoxDecoration(
                            color: visual.goldSoft,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 9),
                        Expanded(
                          child: Text(
                            '${localizer.text(namespace: KefeContentNamespace.caseTitle, id: item.caseId, locale: locale, fallback: item.title)} · ${strings.domainName(item.primaryDomain)}',
                            style: Theme.of(context).textTheme.bodySmall
                                ?.copyWith(
                                  color: visual.onSurfaceStrong.withValues(
                                    alpha: 0.78,
                                  ),
                                ),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: visual.onSurfaceStrong.withValues(alpha: 0.06),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: visual.onSurfaceStrong.withValues(alpha: 0.10),
                  ),
                ),
                child: Text(
                  strings.progressMethodology,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: visual.onSurfaceStrong.withValues(alpha: 0.72),
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (offer.eligible && !state.offerDismissed) ...[
          const SizedBox(height: 12),
          KefeSurface(
            key: const ValueKey('account-offer'),
            tone: KefeSurfaceTone.raised,
            accent: visual.gold,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: visual.subtleGoldSurface,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Icon(
                        Icons.verified_user_outlined,
                        color: visual.gold,
                      ),
                    ),
                    const SizedBox(width: 11),
                    Expanded(
                      child: Text(
                        strings.accountOfferTitle,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w900),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  strings.accountOfferBody,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.mutedForeground,
                    height: 1.4,
                  ),
                ),
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
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: visual.mutedForeground,
                    ),
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
        ],
      ],
    );
  }
}

class _ProgressMetric extends StatelessWidget {
  const _ProgressMetric({
    required this.label,
    required this.value,
    required this.accent,
  });

  final String label;
  final int value;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      label: '$label: $value',
      child: Container(
        constraints: const BoxConstraints(minHeight: 96),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
        decoration: BoxDecoration(
          color: visual.onSurfaceStrong.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: visual.onSurfaceStrong.withValues(alpha: 0.11),
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(color: accent, shape: BoxShape.circle),
            ),
            const SizedBox(height: 7),
            Text(
              '$value',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: visual.onSurfaceStrong,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              maxLines: 2,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.onSurfaceStrong.withValues(alpha: 0.70),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
