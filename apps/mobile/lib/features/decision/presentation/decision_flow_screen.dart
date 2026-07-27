import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/localization/kefe_strings.dart';
import '../application/decision_controller.dart';

class DecisionFlowScreen extends ConsumerStatefulWidget {
  const DecisionFlowScreen({super.key});

  @override
  ConsumerState<DecisionFlowScreen> createState() => _DecisionFlowScreenState();
}

class _DecisionFlowScreenState extends ConsumerState<DecisionFlowScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(decisionControllerProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final state = ref.watch(decisionControllerProvider);

    return Scaffold(
      appBar: AppBar(title: Text(strings.appName)),
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          child: state.loading
              ? Center(key: const ValueKey('loading'), child: Semantics(label: strings.loading, child: const CircularProgressIndicator()))
              : state.caseData == null
                  ? _ErrorState(
                      key: const ValueKey('error'),
                      message: strings.genericError,
                      retryLabel: strings.retry,
                      onRetry: ref.read(decisionControllerProvider.notifier).load,
                    )
                  : _DecisionContent(
                      key: const ValueKey('content'),
                      state: state,
                    ),
        ),
      ),
    );
  }
}

class _DecisionContent extends ConsumerWidget {
  const _DecisionContent({required this.state, super.key});

  final DecisionState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final caseData = state.caseData!;
    final question = caseData.questions.first;
    final controller = ref.read(decisionControllerProvider.notifier);

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(caseData.title, style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 12),
        Text(caseData.summary, style: Theme.of(context).textTheme.bodyLarge),
        const SizedBox(height: 24),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(question.prompt, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 16),
                for (final option in question.options)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Semantics(
                      selected: state.selectedOption == option,
                      button: true,
                      child: ChoiceChip(
                        label: SizedBox(
                          width: double.infinity,
                          child: Text(option, textAlign: TextAlign.center),
                        ),
                        selected: state.selectedOption == option,
                        onSelected: state.reveal == null ? (_) => controller.select(option) : null,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        if (state.reveal == null) ...[
          FilledButton(
            onPressed: state.selectedOption == null || state.submitting ? null : controller.commit,
            child: state.submitting
                ? const SizedBox.square(
                    dimension: 22,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(strings.commit),
          ),
          const SizedBox(height: 8),
          Text(
            state.selectedOption == null ? strings.selectAnswer : strings.commitHelper,
            textAlign: TextAlign.center,
          ),
        ] else
          _RevealCard(state: state),
        if (state.errorCode != null) ...[
          const SizedBox(height: 16),
          Text(
            strings.genericError,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
            textAlign: TextAlign.center,
          ),
        ],
      ],
    );
  }
}

class _RevealCard extends StatelessWidget {
  const _RevealCard({required this.state});

  final DecisionState state;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final reveal = state.reveal!;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(strings.revealTitle, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            for (final entry in reveal.values.entries)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${entry.key} · ${(entry.value * 100).round()}%'),
                    const SizedBox(height: 6),
                    LinearProgressIndicator(value: entry.value),
                  ],
                ),
              ),
            const SizedBox(height: 8),
            Text('${strings.trustedSample} · n=${reveal.sampleSize} · ${reveal.confidence}'),
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.retryLabel, required this.onRetry, super.key});

  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: Text(retryLabel)),
          ],
        ),
      ),
    );
  }
}
