import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../progress/application/progress_controller.dart';
import '../../progress/domain/progress_models.dart';
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
          key: const ValueKey('activity-screen'),
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 30),
          children: [
            _ActivityHeader(strings: strings),
            const SizedBox(height: 10),
            Text(
              strings.activitySubtitle,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                    height: 1.45,
                  ),
            ),
            const SizedBox(height: 18),
            const SavedCasesSection(visible: true),
            const SizedBox(height: 18),
            ...switch (state.uiState) {
              ProgressUiState.idle || ProgressUiState.loading => [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Text(strings.activityLoading),
                    ),
                  ),
                ],
              ProgressUiState.errorRetryable => [
                  _ActivityError(
                    message: strings.activityUnavailable,
                    retryLabel: strings.activityRetry,
                    onRetry: ref.read(progressControllerProvider.notifier).load,
                  ),
                ],
              ProgressUiState.ready =>
                _ready(context, strings, state.envelope!),
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
        Card(
          key: const ValueKey('activity-empty'),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Text(strings.activityEmpty),
          ),
        ),
      ];
    }

    return [
      if (preview) _PreviewNotice(text: strings.activityPreviewNotice),
      if (preview) const SizedBox(height: 14),
      Text(
        strings.activityHistoryTitle,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w900,
            ),
      ),
      const SizedBox(height: 12),
      Card(
        key: const ValueKey('activity-history'),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            children: [
              if (journeys.isNotEmpty)
                for (var index = 0; index < journeys.length; index++) ...[
                  _JourneyTile(item: journeys[index], strings: strings),
                  if (index != journeys.length - 1)
                    const Divider(height: 24),
                ]
              else
                for (var index = 0; index < legacy.length; index++) ...[
                  _LegacyJourneyTile(item: legacy[index], strings: strings),
                  if (index != legacy.length - 1)
                    const Divider(height: 24),
                ],
            ],
          ),
        ),
      ),
    ];
  }
}

class _ActivityHeader extends StatelessWidget {
  const _ActivityHeader({required this.strings});

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
                  strings.activityEyebrow,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: KefeColorTokens.goldSoft,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1.1,
                      ),
                ),
                const SizedBox(height: 7),
                Text(
                  strings.activityTitle,
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
            child: Icon(Icons.history_rounded),
          ),
        ],
      );
}

class _JourneyTile extends StatelessWidget {
  const _JourneyTile({required this.item, required this.strings});

  final MyKefeRecentJourney item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        label: item.title,
        child: InkWell(
          key: ValueKey('activity-case-${item.caseId}'),
          borderRadius: BorderRadius.circular(14),
          onTap: () => context.push('/case/${item.caseId}'),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const CircleAvatar(
                  backgroundColor: Color(0x1FD9B66F),
                  foregroundColor: KefeColorTokens.goldSoft,
                  child: Icon(Icons.balance_outlined),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.title,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                      const SizedBox(height: 7),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          if (item.decisionUpdateCount > 0)
                            Chip(
                              label: Text(
                                strings.activityUpdateCount(
                                  item.decisionUpdateCount,
                                ),
                              ),
                            ),
                          if (item.reflectionCompleted)
                            Chip(label: Text(strings.activityReflected)),
                          if (item.decisionUpdateCount == 0 &&
                              !item.reflectionCompleted)
                            Chip(label: Text(strings.activityCommitted)),
                        ],
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.arrow_forward_rounded),
              ],
            ),
          ),
        ),
      );
}

class _LegacyJourneyTile extends StatelessWidget {
  const _LegacyJourneyTile({required this.item, required this.strings});

  final RecentProgressCase item;
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => ListTile(
        key: ValueKey('activity-case-${item.caseId}'),
        contentPadding: EdgeInsets.zero,
        leading: const CircleAvatar(
          backgroundColor: Color(0x1FD9B66F),
          foregroundColor: KefeColorTokens.goldSoft,
          child: Icon(Icons.balance_outlined),
        ),
        title: Text(
          item.title,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        subtitle: Text(strings.activityCommitted),
        trailing: const Icon(Icons.arrow_forward_rounded),
        onTap: () => context.push('/case/${item.caseId}'),
      );
}

class _ActivityError extends StatelessWidget {
  const _ActivityError({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
  });

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(message),
              const SizedBox(height: 12),
              OutlinedButton(onPressed: onRetry, child: Text(retryLabel)),
            ],
          ),
        ),
      );
}

class _PreviewNotice extends StatelessWidget {
  const _PreviewNotice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Container(
        key: const ValueKey('activity-preview-notice'),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: KefeColorTokens.rules.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: KefeColorTokens.rules.withValues(alpha: 0.22),
          ),
        ),
        child: Text(
          text,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: KefeColorTokens.textMutedDark,
              ),
        ),
      );
}

extension ActivityStrings on KefeStrings {
  bool get _activityIsTurkish => locale.languageCode == 'tr';

  String get activityEyebrow =>
      _activityIsTurkish ? 'AKTİVİTE' : 'ACTIVITY';
  String get activityTitle => _activityIsTurkish
      ? 'Kararlarına geri dön.'
      : 'Return to your decisions.';
  String get activitySubtitle => _activityIsTurkish
      ? 'Kaydettiğin vakalar, geçmiş kararların ve yeniden tartım izlerin burada birbirinden ayrı görünür.'
      : 'Saved Cases, past decisions and revisit history stay distinct here.';
  String get activityLoading => _activityIsTurkish
      ? 'Aktiviten yükleniyor…'
      : 'Loading your activity…';
  String get activityUnavailable => _activityIsTurkish
      ? 'Aktivite şu anda yüklenemedi.'
      : 'Activity is currently unavailable.';
  String get activityRetry => _activityIsTurkish ? 'Tekrar dene' : 'Retry';
  String get activityEmpty => _activityIsTurkish
      ? 'Henüz geçmiş bir tartımın yok. İlk kararından sonra burada görünecek.'
      : 'You have no past weighs yet. They will appear after your first decision.';
  String get activityHistoryTitle =>
      _activityIsTurkish ? 'Karar geçmişin' : 'Decision history';
  String get activityCommitted =>
      _activityIsTurkish ? 'Karar verildi' : 'Decision committed';
  String get activityReflected =>
      _activityIsTurkish ? 'Yansıma tamamlandı' : 'Reflection completed';
  String activityUpdateCount(int count) => _activityIsTurkish
      ? '$count yeniden tartım'
      : '$count decision update${count == 1 ? '' : 's'}';
  String get activityPreviewNotice => _activityIsTurkish
      ? 'Bu ekrandaki karar geçmişi Product Preview örnek verisidir; canlı kullanıcı verisi değildir.'
      : 'Decision history on this screen is Product Preview sample data, not live user data.';
}
