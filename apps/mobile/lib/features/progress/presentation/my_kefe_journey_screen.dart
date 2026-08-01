import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../saved_cases/presentation/saved_cases_section.dart';
import '../application/progress_controller.dart';
import '../domain/progress_models.dart';
import 'progress_async_state_surface.dart';
import 'progress_strings.dart';

class MyKefeJourneyScreen extends ConsumerStatefulWidget {
  const MyKefeJourneyScreen({this.embedded = false, super.key});

  final bool embedded;

  @override
  ConsumerState<MyKefeJourneyScreen> createState() =>
      _MyKefeJourneyScreenState();
}

class _MyKefeJourneyScreenState extends ConsumerState<MyKefeJourneyScreen> {
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
    final body = SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: ref.read(progressControllerProvider.notifier).load,
        child: ListView(
          key: const ValueKey('my-kefe-journey'),
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 30),
          children: [
            _Header(strings: strings),
            const SizedBox(height: 18),
            const SavedCasesSection(),
            ...switch (state.uiState) {
              ProgressUiState.idle || ProgressUiState.loading => [
                ProgressAsyncStateSurface.loading(
                  surfaceKey: 'my-kefe-loading',
                  message: strings.progressLoading,
                ),
              ],
              ProgressUiState.errorRetryable => [
                ProgressAsyncStateSurface.error(
                  surfaceKey: 'my-kefe-error',
                  retryKey: 'my-kefe-retry',
                  message: strings.progressUnavailable,
                  retryLabel: strings.progressRetry,
                  onRetry: ref.read(progressControllerProvider.notifier).load,
                ),
              ],
              ProgressUiState.ready => _ready(
                context,
                strings,
                state.envelope!,
              ),
            },
          ],
        ),
      ),
    );
    return widget.embedded ? body : Scaffold(body: body);
  }

  List<Widget> _ready(
    BuildContext context,
    KefeStrings strings,
    ProgressEnvelope envelope,
  ) {
    final progress = envelope.progress;
    final journey = envelope.journey;
    final preview =
        envelope.methodology['data_mode'] == 'DETERMINISTIC_PREVIEW';
    if (progress.meaningfulWeighCount == 0) {
      return [
        if (preview) _Notice(text: strings.journeyPreviewNotice),
        if (preview) const SizedBox(height: 14),
        KefeSurface(
          key: const ValueKey('my-kefe-empty'),
          tone: KefeSurfaceTone.raised,
          child: Text(strings.journeyEmpty),
        ),
        const SizedBox(height: 14),
        _Footnote(strings: strings),
      ];
    }

    return [
      if (preview)
        _Notice(
          key: const ValueKey('my-kefe-preview-notice'),
          text: strings.journeyPreviewNotice,
        ),
      if (preview) const SizedBox(height: 14),
      _Overview(progress: progress, journey: journey, strings: strings),
      if (journey.domainActivity.isNotEmpty) ...[
        const SizedBox(height: 18),
        _Domains(items: journey.domainActivity, strings: strings),
      ],
      if (journey.recentJourneys.isNotEmpty) ...[
        const SizedBox(height: 18),
        _Journeys(items: journey.recentJourneys, strings: strings),
      ] else if (progress.recentCases.isNotEmpty) ...[
        const SizedBox(height: 18),
        _LegacyRecent(progress: progress, strings: strings),
      ],
      const SizedBox(height: 18),
      _Footnote(strings: strings),
    ];
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.premium,
      accent: visual.gold,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                KefeEyebrow(
                  strings.journeyEyebrow,
                  icon: Icons.timeline_rounded,
                ),
                const SizedBox(height: 9),
                Text(
                  strings.journeyTitle,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                    height: 1.08,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  strings.journeySubtitle,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.onSurfaceStrong.withValues(alpha: 0.76),
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: visual.gold.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: visual.goldSoft.withValues(alpha: 0.34),
              ),
            ),
            child: Icon(Icons.timeline_rounded, color: visual.goldSoft),
          ),
        ],
      ),
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({
    required this.progress,
    required this.journey,
    required this.strings,
  });

  final MyKefeProgress progress;
  final MyKefeJourney journey;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.premium,
      accent: visual.gold,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
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
                child: _Metric(
                  key: const ValueKey('my-kefe-weigh-count'),
                  value: progress.meaningfulWeighCount,
                  label: strings.progressWeighs,
                  icon: Icons.balance_rounded,
                  accent: visual.goldSoft,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _Metric(
                  key: const ValueKey('my-kefe-update-count'),
                  value: journey.decisionUpdateCount,
                  label: strings.journeyRevisits,
                  icon: Icons.change_circle_outlined,
                  accent: visual.rules,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _Metric(
                  key: const ValueKey('my-kefe-reflection-count'),
                  value: journey.reflectionCompletionCount,
                  label: strings.journeyReflections,
                  icon: Icons.auto_awesome_outlined,
                  accent: visual.empathy,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.value,
    required this.label,
    required this.icon,
    required this.accent,
    super.key,
  });

  final int value;
  final String label;
  final IconData icon;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Semantics(
      label: '$label: $value',
      child: Container(
        constraints: const BoxConstraints(minHeight: 108),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 11),
        decoration: BoxDecoration(
          color: visual.onSurfaceStrong.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(17),
          border: Border.all(
            color: visual.onSurfaceStrong.withValues(alpha: 0.12),
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 18, color: accent),
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

class _Domains extends StatelessWidget {
  const _Domains({required this.items, required this.strings});

  final List<MyKefeDomainActivity> items;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final max = items.fold<int>(
      1,
      (m, e) => e.committedWeighCount > m ? e.committedWeighCount : m,
    );
    return KefeSurface(
      key: const ValueKey('my-kefe-domain-activity'),
      tone: KefeSurfaceTone.raised,
      accent: visual.rules,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          KefeEyebrow(
            strings.journeyDomainActivity,
            icon: Icons.grid_view_rounded,
            color: visual.rules,
          ),
          const SizedBox(height: 16),
          for (var i = 0; i < items.length; i++) ...[
            Row(
              children: [
                Expanded(
                  child: Text(
                    strings.domainName(items[i].primaryDomain),
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                Text(
                  strings.journeyWeighCount(items[i].committedWeighCount),
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: visual.mutedForeground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 7),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                value: items[i].committedWeighCount / max,
                minHeight: 7,
                color: visual.rules,
                backgroundColor: visual.surfaceSunken,
              ),
            ),
            if (i != items.length - 1) const SizedBox(height: 14),
          ],
        ],
      ),
    );
  }
}

class _Journeys extends ConsumerWidget {
  const _Journeys({required this.items, required this.strings});

  final List<MyKefeRecentJourney> items;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    return KefeSurface(
      key: const ValueKey('my-kefe-recent-journeys'),
      tone: KefeSurfaceTone.raised,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          KefeEyebrow(strings.journeyRecent, icon: Icons.history_rounded),
          const SizedBox(height: 14),
          for (var i = 0; i < items.length; i++) ...[
            Container(
              padding: const EdgeInsets.all(13),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(17),
                border: Border.all(color: visual.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    strings.domainName(items[i].primaryDomain),
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: visual.gold,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    localizer.text(
                      namespace: KefeContentNamespace.caseTitle,
                      id: items[i].caseId,
                      locale: locale,
                      fallback: items[i].title,
                    ),
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  if (items[i].decisionUpdateCount > 0 ||
                      items[i].reflectionCompleted) ...[
                    const SizedBox(height: 9),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        if (items[i].decisionUpdateCount > 0)
                          _JourneyPill(
                            label: strings.journeyUpdateCount(
                              items[i].decisionUpdateCount,
                            ),
                            color: visual.rules,
                          ),
                        if (items[i].reflectionCompleted)
                          _JourneyPill(
                            label: strings.journeyReflected,
                            color: visual.gold,
                          ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            if (i != items.length - 1) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _LegacyRecent extends ConsumerWidget {
  const _LegacyRecent({required this.progress, required this.strings});

  final MyKefeProgress progress;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          KefeEyebrow(strings.progressRecent, icon: Icons.history_rounded),
          const SizedBox(height: 12),
          for (final item in progress.recentCases)
            Padding(
              padding: const EdgeInsets.only(bottom: 9),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    margin: const EdgeInsets.only(top: 6),
                    decoration: BoxDecoration(
                      color: visual.gold,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      '${localizer.text(namespace: KefeContentNamespace.caseTitle, id: item.caseId, locale: locale, fallback: item.title)} · ${strings.domainName(item.primaryDomain)}',
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _JourneyPill extends StatelessWidget {
  const _JourneyPill({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.10),
      borderRadius: BorderRadius.circular(999),
      border: Border.all(color: color.withValues(alpha: 0.20)),
    ),
    child: Text(
      label,
      style: Theme.of(context).textTheme.labelSmall?.copyWith(
        color: color,
        fontWeight: FontWeight.w800,
      ),
    ),
  );
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, super.key});

  final String text;

  @override
  Widget build(BuildContext context) => KefeSurface(
    padding: const EdgeInsets.all(13),
    tone: KefeSurfaceTone.sunken,
    accent: context.kefeVisual.rules,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.science_outlined, size: 18, color: context.kefeVisual.rules),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: context.kefeVisual.mutedForeground,
              height: 1.4,
            ),
          ),
        ),
      ],
    ),
  );
}

class _Footnote extends StatelessWidget {
  const _Footnote({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => KefeSurface(
    key: const ValueKey('my-kefe-no-inference-note'),
    tone: KefeSurfaceTone.sunken,
    padding: const EdgeInsets.all(15),
    accent: context.kefeVisual.gold,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          Icons.visibility_outlined,
          size: 18,
          color: context.kefeVisual.gold,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            strings.journeyNonInferenceNote,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: context.kefeVisual.mutedForeground,
              height: 1.4,
            ),
          ),
        ),
      ],
    ),
  );
}
