import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../explore/application/explore_controller.dart';
import '../../progress/application/progress_controller.dart';
import '../../progress/domain/progress_models.dart';
import '../../progress/presentation/progress_async_state_surface.dart';
import '../../saved_cases/application/saved_cases_controller.dart';
import '../../saved_cases/presentation/saved_cases_section.dart';

class ActivityScreen extends ConsumerStatefulWidget {
  const ActivityScreen({this.embedded = false, super.key});

  final bool embedded;

  @override
  ConsumerState<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends ConsumerState<ActivityScreen> {
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
        onRefresh: () async {
          await Future.wait([
            ref.read(progressControllerProvider.notifier).load(),
            ref.read(savedCasesControllerProvider.notifier).load(),
            ref.read(exploreControllerProvider.notifier).load(),
          ]);
        },
        child: ListView(
          key: const ValueKey('activity-screen'),
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 30),
          children: [
            _ActivityHero(strings: strings),
            const SizedBox(height: 18),
            const SavedCasesSection(visible: true, lifecycleUpdates: true),
            const SizedBox(height: 18),
            ...switch (state.uiState) {
              ProgressUiState.idle || ProgressUiState.loading => [
                ProgressAsyncStateSurface.loading(
                  surfaceKey: 'activity-loading',
                  message: strings.activityLoading,
                ),
              ],
              ProgressUiState.errorRetryable => [
                ProgressAsyncStateSurface.error(
                  surfaceKey: 'activity-error',
                  retryKey: 'activity-retry',
                  message: strings.activityUnavailable,
                  retryLabel: strings.activityRetry,
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
    final preview =
        envelope.methodology['data_mode'] == 'DETERMINISTIC_PREVIEW';
    final journeys = envelope.journey.recentJourneys;
    final legacy = envelope.progress.recentCases;

    if (journeys.isEmpty && legacy.isEmpty) {
      return [
        if (preview) _PreviewNotice(text: strings.activityPreviewNotice),
        if (preview) const SizedBox(height: 14),
        KefeSurface(
          key: const ValueKey('activity-empty'),
          tone: KefeSurfaceTone.raised,
          child: Text(strings.activityEmpty),
        ),
      ];
    }

    return [
      if (preview) _PreviewNotice(text: strings.activityPreviewNotice),
      if (preview) const SizedBox(height: 16),
      KefeEyebrow(
        strings.activityHistoryTitle,
        icon: Icons.history_toggle_off_rounded,
      ),
      const SizedBox(height: 10),
      KefeSurface(
        key: const ValueKey('activity-history'),
        tone: KefeSurfaceTone.raised,
        child: Column(
          children: [
            if (journeys.isNotEmpty)
              for (var index = 0; index < journeys.length; index++) ...[
                _JourneyTile(item: journeys[index], strings: strings),
                if (index != journeys.length - 1) const SizedBox(height: 10),
              ]
            else
              for (var index = 0; index < legacy.length; index++) ...[
                _LegacyJourneyTile(item: legacy[index], strings: strings),
                if (index != legacy.length - 1) const SizedBox(height: 10),
              ],
          ],
        ),
      ),
    ];
  }
}

class _ActivityHero extends StatelessWidget {
  const _ActivityHero({required this.strings});

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
                  strings.activityEyebrow,
                  icon: Icons.history_rounded,
                ),
                const SizedBox(height: 9),
                Text(
                  strings.activityTitle,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                    height: 1.08,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  strings.activitySubtitle,
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
            child: ExcludeSemantics(
              child: Icon(Icons.history_rounded, color: visual.goldSoft),
            ),
          ),
        ],
      ),
    );
  }
}

class _JourneyTile extends ConsumerWidget {
  const _JourneyTile({required this.item, required this.strings});

  final MyKefeRecentJourney item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    final displayTitle = localizer.text(
      namespace: KefeContentNamespace.caseTitle,
      id: item.caseId,
      locale: locale,
      fallback: item.title,
    );

    return Semantics(
      button: true,
      label: displayTitle,
      child: Material(
        color: visual.surfaceSunken,
        borderRadius: BorderRadius.circular(18),
        child: InkWell(
          key: ValueKey('activity-case-${item.caseId}'),
          borderRadius: BorderRadius.circular(18),
          onTap: () => context.push('/case/${item.caseId}'),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HistoryIcon(icon: Icons.balance_outlined, color: visual.gold),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        displayTitle,
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 9),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          if (item.decisionUpdateCount > 0)
                            _HistoryPill(
                              label: strings.activityUpdateCount(
                                item.decisionUpdateCount,
                              ),
                              color: visual.rules,
                            ),
                          if (item.reflectionCompleted)
                            _HistoryPill(
                              label: strings.activityReflected,
                              color: visual.gold,
                            ),
                          if (item.decisionUpdateCount == 0 &&
                              !item.reflectionCompleted)
                            _HistoryPill(
                              label: strings.activityCommitted,
                              color: visual.success,
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                ExcludeSemantics(
                  child: Icon(
                    Icons.arrow_forward_rounded,
                    size: 20,
                    color: visual.mutedForeground,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LegacyJourneyTile extends ConsumerWidget {
  const _LegacyJourneyTile({required this.item, required this.strings});

  final RecentProgressCase item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    final displayTitle = localizer.text(
      namespace: KefeContentNamespace.caseTitle,
      id: item.caseId,
      locale: locale,
      fallback: item.title,
    );

    return Semantics(
      button: true,
      label: displayTitle,
      child: Material(
        color: visual.surfaceSunken,
        borderRadius: BorderRadius.circular(18),
        child: InkWell(
          key: ValueKey('activity-case-${item.caseId}'),
          borderRadius: BorderRadius.circular(18),
          onTap: () => context.push('/case/${item.caseId}'),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                _HistoryIcon(icon: Icons.balance_outlined, color: visual.gold),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        displayTitle,
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 7),
                      _HistoryPill(
                        label: strings.activityCommitted,
                        color: visual.success,
                      ),
                    ],
                  ),
                ),
                ExcludeSemantics(
                  child: Icon(
                    Icons.arrow_forward_rounded,
                    size: 20,
                    color: visual.mutedForeground,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _HistoryIcon extends StatelessWidget {
  const _HistoryIcon({required this.icon, required this.color});

  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Icon(icon, size: 20, color: color),
    ),
  );
}

class _HistoryPill extends StatelessWidget {
  const _HistoryPill({required this.label, required this.color});

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

class _PreviewNotice extends StatelessWidget {
  const _PreviewNotice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => KefeSurface(
    key: const ValueKey('activity-preview-notice'),
    tone: KefeSurfaceTone.sunken,
    padding: const EdgeInsets.all(13),
    accent: context.kefeVisual.rules,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ExcludeSemantics(
          child: Icon(
            Icons.science_outlined,
            size: 18,
            color: context.kefeVisual.rules,
          ),
        ),
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
