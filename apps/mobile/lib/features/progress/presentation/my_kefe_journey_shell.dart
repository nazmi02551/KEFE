part of 'my_kefe_journey_screen.dart';

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
      const SizedBox(height: 18),
      _ReportEntry(
        momentCount: envelope.personalReport.moments.length,
        strings: strings,
      ),
      const SizedBox(height: 18),
      _NextStep(journey: journey, strings: strings),
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
