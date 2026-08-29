import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_content_localizer.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/progress_controller.dart';
import '../domain/progress_models.dart';
import 'progress_async_state_surface.dart';
import 'progress_strings.dart';

class MyKefePersonalReportScreen extends ConsumerStatefulWidget {
  const MyKefePersonalReportScreen({super.key});

  @override
  ConsumerState<MyKefePersonalReportScreen> createState() =>
      _MyKefePersonalReportScreenState();
}

class _MyKefePersonalReportScreenState
    extends ConsumerState<MyKefePersonalReportScreen> {
  @override
  void initState() {
    super.initState();
    if (ref.read(progressControllerProvider).uiState == ProgressUiState.idle) {
      Future<void>.microtask(
        () => ref.read(progressControllerProvider.notifier).load(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final state = ref.watch(progressControllerProvider);
    return Scaffold(
      appBar: AppBar(title: Text(strings.reportTitle)),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: ref.read(progressControllerProvider.notifier).load,
          child: ListView(
            key: const ValueKey('my-kefe-personal-report'),
            padding: const EdgeInsets.fromLTRB(18, 14, 18, 30),
            children: switch (state.uiState) {
              ProgressUiState.idle || ProgressUiState.loading => [
                ProgressAsyncStateSurface.loading(
                  surfaceKey: 'my-kefe-report-loading',
                  message: strings.progressLoading,
                ),
              ],
              ProgressUiState.errorRetryable => [
                ProgressAsyncStateSurface.error(
                  surfaceKey: 'my-kefe-report-error',
                  retryKey: 'my-kefe-report-retry',
                  message: strings.progressUnavailable,
                  retryLabel: strings.progressRetry,
                  onRetry: ref.read(progressControllerProvider.notifier).load,
                ),
              ],
              ProgressUiState.ready => _ready(strings, state.envelope!),
            },
          ),
        ),
      ),
    );
  }

  List<Widget> _ready(KefeStrings strings, ProgressEnvelope envelope) {
    final preview =
        envelope.methodology['data_mode'] == 'DETERMINISTIC_PREVIEW';
    final moments = envelope.personalReport.moments;
    return [
      _ReportHero(strings: strings),
      if (preview) ...[
        const SizedBox(height: 14),
        _ReportNotice(text: strings.reportPreviewNotice),
      ],
      const SizedBox(height: 18),
      _ReportSnapshot(envelope: envelope, strings: strings),
      const SizedBox(height: 18),
      if (moments.isEmpty)
        KefeSurface(
          key: const ValueKey('my-kefe-report-empty'),
          tone: KefeSurfaceTone.raised,
          child: Text(strings.reportEmpty),
        )
      else
        _ReportTimeline(moments: moments, strings: strings),
      const SizedBox(height: 18),
      _ReportBoundary(text: strings.reportNonInference),
    ];
  }
}

class _ReportHero extends StatelessWidget {
  const _ReportHero({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      key: const ValueKey('my-kefe-report-hero'),
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
                  strings.reportEyebrow,
                  icon: Icons.route_rounded,
                ),
                const SizedBox(height: 10),
                Text(
                  strings.reportHeroTitle,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: visual.onSurfaceStrong,
                    fontWeight: FontWeight.w900,
                    height: 1.12,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  strings.reportHeroSubtitle,
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
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: visual.gold.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: visual.goldSoft.withValues(alpha: 0.32),
              ),
            ),
            child: Icon(Icons.history_toggle_off_rounded, color: visual.goldSoft),
          ),
        ],
      ),
    );
  }
}

class _ReportSnapshot extends StatelessWidget {
  const _ReportSnapshot({required this.envelope, required this.strings});

  final ProgressEnvelope envelope;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final dates = MaterialLocalizations.of(context);
    final first = envelope.progress.firstCommittedAt;
    final last = envelope.progress.lastCommittedAt;
    final dateRange = first == null || last == null
        ? '—'
        : '${dates.formatMediumDate(first.toLocal())} — ${dates.formatMediumDate(last.toLocal())}';
    return KefeSurface(
      key: const ValueKey('my-kefe-report-snapshot'),
      tone: KefeSurfaceTone.raised,
      accent: visual.rules,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          KefeEyebrow(
            strings.reportSnapshot,
            icon: Icons.assessment_outlined,
            color: visual.rules,
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _ReportMetric(
                  value: envelope.progress.distinctCaseCount,
                  label: strings.progressCases,
                  color: visual.gold,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _ReportMetric(
                  value: envelope.journey.decisionUpdateCount,
                  label: strings.journeyRevisits,
                  color: visual.rules,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _ReportMetric(
                  value: envelope.journey.reflectionCompletionCount,
                  label: strings.journeyReflections,
                  color: visual.empathy,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            strings.reportDateRange,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: visual.mutedForeground,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            dateRange,
            key: const ValueKey('my-kefe-report-date-range'),
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

class _ReportMetric extends StatelessWidget {
  const _ReportMetric({
    required this.value,
    required this.label,
    required this.color,
  });

  final int value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Semantics(
    label: '$label: $value',
    child: Container(
      constraints: const BoxConstraints(minHeight: 82),
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: color.withValues(alpha: 0.18)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '$value',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: color,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            maxLines: 2,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: context.kefeVisual.mutedForeground,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    ),
  );
}

class _ReportTimeline extends StatelessWidget {
  const _ReportTimeline({required this.moments, required this.strings});

  final List<MyKefeReportMoment> moments;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => KefeSurface(
    key: const ValueKey('my-kefe-report-timeline'),
    tone: KefeSurfaceTone.raised,
    padding: const EdgeInsets.all(16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KefeEyebrow(strings.reportMoments, icon: Icons.timeline_rounded),
        const SizedBox(height: 14),
        for (var index = 0; index < moments.length; index++) ...[
          _ReportMomentCard(
            key: ValueKey('my-kefe-report-moment-$index'),
            moment: moments[index],
            strings: strings,
          ),
          if (index != moments.length - 1) const SizedBox(height: 10),
        ],
      ],
    ),
  );
}

class _ReportMomentCard extends ConsumerWidget {
  const _ReportMomentCard({
    required this.moment,
    required this.strings,
    super.key,
  });

  final MyKefeReportMoment moment;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final visual = context.kefeVisual;
    final locale = Localizations.localeOf(context);
    final localizer = ref.watch(kefeContentLocalizerProvider);
    final title = localizer.text(
      namespace: KefeContentNamespace.caseTitle,
      id: moment.caseId,
      locale: locale,
      fallback: moment.title,
    );
    final local = moment.occurredAt.toLocal();
    final dates = MaterialLocalizations.of(context);
    final date = dates.formatMediumDate(local);
    final time = dates.formatTimeOfDay(TimeOfDay.fromDateTime(local));
    final presentation = _momentPresentation(visual);
    final label = _momentLabel();
    return Semantics(
      button: true,
      label: '$label. $title. $date, $time. ${strings.reportOpenCase}',
      child: KefeSurface(
        tone: KefeSurfaceTone.sunken,
        padding: EdgeInsets.zero,
        borderRadius: 17,
        accent: presentation.color,
        child: InkWell(
          onTap: () => context.push('/case/${moment.caseId}'),
          child: Padding(
            padding: const EdgeInsets.all(13),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: presentation.color.withValues(alpha: 0.11),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    presentation.icon,
                    size: 19,
                    color: presentation.color,
                  ),
                ),
                const SizedBox(width: 11),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        label,
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: presentation.color,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                          height: 1.3,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${strings.domainName(moment.primaryDomain)} · $date · $time',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: visual.mutedForeground,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Icon(
                  Icons.arrow_forward_ios_rounded,
                  size: 16,
                  color: visual.mutedForeground,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _momentLabel() => switch (moment.type) {
    MyKefeReportMomentType.initialCommit => strings.reportInitialCommit,
    MyKefeReportMomentType.decisionUpdate =>
      '${strings.reportDecisionUpdate} · ${strings.reportRevision(moment.revisionNo!)}',
    MyKefeReportMomentType.reflectionCompleted =>
      strings.reportReflectionCompleted,
  };

  ({IconData icon, Color color}) _momentPresentation(KefeVisualTheme visual) =>
      switch (moment.type) {
        MyKefeReportMomentType.initialCommit => (
          icon: Icons.lock_outline_rounded,
          color: visual.gold,
        ),
        MyKefeReportMomentType.decisionUpdate => (
          icon: Icons.change_circle_outlined,
          color: visual.rules,
        ),
        MyKefeReportMomentType.reflectionCompleted => (
          icon: Icons.auto_awesome_outlined,
          color: visual.empathy,
        ),
      };
}

class _ReportNotice extends StatelessWidget {
  const _ReportNotice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => KefeSurface(
    key: const ValueKey('my-kefe-report-preview-notice'),
    tone: KefeSurfaceTone.sunken,
    padding: const EdgeInsets.all(13),
    accent: context.kefeVisual.rules,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.science_outlined, size: 18, color: context.kefeVisual.rules),
        const SizedBox(width: 10),
        Expanded(child: Text(text)),
      ],
    ),
  );
}

class _ReportBoundary extends StatelessWidget {
  const _ReportBoundary({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => KefeSurface(
    key: const ValueKey('my-kefe-report-no-inference'),
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
            text,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: context.kefeVisual.mutedForeground,
              height: 1.45,
            ),
          ),
        ),
      ],
    ),
  );
}
