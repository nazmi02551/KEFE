import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/progress_controller.dart';
import '../domain/progress_models.dart';
import 'progress_strings.dart';

class MyKefeJourneyScreen extends ConsumerStatefulWidget {
  const MyKefeJourneyScreen({this.embedded = false, super.key});

  final bool embedded;

  @override
  ConsumerState<MyKefeJourneyScreen> createState() => _MyKefeJourneyScreenState();
}

class _MyKefeJourneyScreenState extends ConsumerState<MyKefeJourneyScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(progressControllerProvider.notifier).load());
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
            const SizedBox(height: 10),
            Text(
              strings.journeySubtitle,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                    height: 1.45,
                  ),
            ),
            const SizedBox(height: 18),
            ...switch (state.uiState) {
              ProgressUiState.idle || ProgressUiState.loading => [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Text(strings.progressLoading),
                    ),
                  ),
                ],
              ProgressUiState.errorRetryable => [
                  Card(
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
                ],
              ProgressUiState.ready => _ready(context, strings, state.envelope!),
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
    final preview = envelope.methodology['data_mode'] == 'DETERMINISTIC_PREVIEW';
    if (progress.meaningfulWeighCount == 0) {
      return [
        if (preview) _Notice(text: strings.journeyPreviewNotice),
        if (preview) const SizedBox(height: 14),
        Card(child: Padding(padding: const EdgeInsets.all(20), child: Text(strings.journeyEmpty))),
        const SizedBox(height: 14),
        _Footnote(strings: strings),
      ];
    }

    return [
      if (preview) _Notice(key: const ValueKey('my-kefe-preview-notice'), text: strings.journeyPreviewNotice),
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
  Widget build(BuildContext context) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  strings.journeyEyebrow,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: KefeColorTokens.goldSoft,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1.1,
                      ),
                ),
                const SizedBox(height: 7),
                Text(
                  strings.journeyTitle,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                        height: 1.08,
                      ),
                ),
              ],
            ),
          ),
          const CircleAvatar(
            backgroundColor: Color(0x222CC9BC),
            foregroundColor: KefeColorTokens.goldSoft,
            child: Icon(Icons.timeline_rounded),
          ),
        ],
      );
}

class _Overview extends StatelessWidget {
  const _Overview({required this.progress, required this.journey, required this.strings});
  final MyKefeProgress progress;
  final MyKefeJourney journey;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: KefeColorTokens.gold.withValues(alpha: 0.24)),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF122640), Color(0xFF111823), Color(0xFF281B24)],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(strings.progressReadiness(progress.readiness), style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 15),
            Row(
              children: [
                Expanded(child: _Metric(key: const ValueKey('my-kefe-weigh-count'), value: progress.meaningfulWeighCount, label: strings.progressWeighs, icon: Icons.balance_rounded)),
                const SizedBox(width: 8),
                Expanded(child: _Metric(key: const ValueKey('my-kefe-update-count'), value: journey.decisionUpdateCount, label: strings.journeyRevisits, icon: Icons.change_circle_outlined)),
                const SizedBox(width: 8),
                Expanded(child: _Metric(key: const ValueKey('my-kefe-reflection-count'), value: journey.reflectionCompletionCount, label: strings.journeyReflections, icon: Icons.auto_awesome_outlined)),
              ],
            ),
          ],
        ),
      );
}

class _Metric extends StatelessWidget {
  const _Metric({required this.value, required this.label, required this.icon, super.key});
  final int value;
  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Container(
        constraints: const BoxConstraints(minHeight: 105),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: KefeColorTokens.surfaceDark.withValues(alpha: 0.78),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: KefeColorTokens.borderDark),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 18, color: KefeColorTokens.goldSoft),
            const SizedBox(height: 7),
            Text('$value', style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: KefeColorTokens.goldSoft, fontWeight: FontWeight.w900)),
            Text(label, maxLines: 2, textAlign: TextAlign.center, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: KefeColorTokens.textMutedDark)),
          ],
        ),
      );
}

class _Domains extends StatelessWidget {
  const _Domains({required this.items, required this.strings});
  final List<MyKefeDomainActivity> items;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    final max = items.fold<int>(1, (m, e) => e.committedWeighCount > m ? e.committedWeighCount : m);
    return Card(
      key: const ValueKey('my-kefe-domain-activity'),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(strings.journeyDomainActivity, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 14),
            for (var i = 0; i < items.length; i++) ...[
              Row(children: [Expanded(child: Text(_domainLabel(items[i].primaryDomain, strings.locale.languageCode))), Text(strings.journeyWeighCount(items[i].committedWeighCount), style: Theme.of(context).textTheme.labelSmall)]),
              const SizedBox(height: 6),
              LinearProgressIndicator(value: items[i].committedWeighCount / max, minHeight: 6),
              if (i != items.length - 1) const SizedBox(height: 12),
            ],
          ],
        ),
      ),
    );
  }
}

class _Journeys extends StatelessWidget {
  const _Journeys({required this.items, required this.strings});
  final List<MyKefeRecentJourney> items;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Card(
        key: const ValueKey('my-kefe-recent-journeys'),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(strings.journeyRecent, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
              const SizedBox(height: 12),
              for (var i = 0; i < items.length; i++) ...[
                Text(_domainLabel(items[i].primaryDomain, strings.locale.languageCode), style: Theme.of(context).textTheme.labelSmall?.copyWith(color: KefeColorTokens.goldSoft, fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text(items[i].title, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700)),
                if (items[i].decisionUpdateCount > 0 || items[i].reflectionCompleted) ...[
                  const SizedBox(height: 7),
                  Wrap(
                    spacing: 8,
                    children: [
                      if (items[i].decisionUpdateCount > 0) Chip(label: Text(strings.journeyUpdateCount(items[i].decisionUpdateCount))),
                      if (items[i].reflectionCompleted) Chip(label: Text(strings.journeyReflected)),
                    ],
                  ),
                ],
                if (i != items.length - 1) const Divider(height: 24),
              ],
            ],
          ),
        ),
      );
}

class _LegacyRecent extends StatelessWidget {
  const _LegacyRecent({required this.progress, required this.strings});
  final MyKefeProgress progress;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(strings.progressRecent, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 10),
              for (final item in progress.recentCases) Padding(padding: const EdgeInsets.only(bottom: 7), child: Text('• ${item.title} · ${_domainLabel(item.primaryDomain, strings.locale.languageCode)}')),
            ],
          ),
        ),
      );
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, super.key});
  final String text;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: KefeColorTokens.rules.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: KefeColorTokens.rules.withValues(alpha: 0.22)),
        ),
        child: Text(text, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: KefeColorTokens.textMutedDark)),
      );
}

class _Footnote extends StatelessWidget {
  const _Footnote({required this.strings});
  final KefeStrings strings;
  @override
  Widget build(BuildContext context) => Container(
        key: const ValueKey('my-kefe-no-inference-note'),
        padding: const EdgeInsets.all(15),
        decoration: BoxDecoration(color: KefeColorTokens.surfaceDark, borderRadius: BorderRadius.circular(16), border: Border.all(color: KefeColorTokens.borderDark)),
        child: Text(strings.journeyNonInferenceNote, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: KefeColorTokens.textMutedDark, height: 1.4)),
      );
}

String _domainLabel(String domain, String languageCode) {
  final tr = languageCode == 'tr';
  return switch (domain) {
    'DAILY_LIFE' => tr ? 'Günlük yaşam' : 'Daily life',
    'TECHNOLOGY' => tr ? 'Teknoloji' : 'Technology',
    'SPORTS' => tr ? 'Spor' : 'Sports',
    'CIVIC' => tr ? 'Kamusal' : 'Civic',
    'WORK_ECONOMY' => tr ? 'İş & Ekonomi' : 'Work & Economy',
    'EDUCATION' => tr ? 'Eğitim' : 'Education',
    _ => domain.replaceAll('_', ' '),
  };
}
