import 'package:flutter/material.dart';

import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_models.dart';

class PerspectiveSection extends StatelessWidget {
  const PerspectiveSection({
    required this.state,
    required this.result,
    required this.reasonPendingModeration,
    required this.onRetry,
    super.key,
  });

  final PerspectiveUiState state;
  final PerspectiveResult? result;
  final bool reasonPendingModeration;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    if (state == PerspectiveUiState.idle) {
      return const SizedBox.shrink();
    }

    return Card(
      key: const ValueKey('perspective-section'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              strings.perspectiveTitle,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            if (reasonPendingModeration) ...[
              const SizedBox(height: 12),
              Semantics(
                liveRegion: true,
                child: Text(
                  strings.reasonPendingModeration,
                  key: const ValueKey('reason-pending-moderation'),
                ),
              ),
            ],
            const SizedBox(height: 12),
            switch (state) {
              PerspectiveUiState.loading => _LoadingState(strings: strings),
              PerspectiveUiState.errorRetryable => _RetryState(
                  strings: strings,
                  onRetry: onRetry,
                ),
              PerspectiveUiState.ready ||
              PerspectiveUiState.clusterPending ||
              PerspectiveUiState.degradedCurated => _LoadedState(
                  state: state,
                  result: result,
                ),
              PerspectiveUiState.idle => const SizedBox.shrink(),
            },
          ],
        ),
      ),
    );
  }
}

class _LoadingState extends StatelessWidget {
  const _LoadingState({required this.strings});

  final KefeStrings strings;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: strings.perspectiveLoading,
      liveRegion: true,
      child: Row(
        children: [
          const SizedBox.square(
            dimension: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(strings.perspectiveLoading)),
        ],
      ),
    );
  }
}

class _RetryState extends StatelessWidget {
  const _RetryState({required this.strings, required this.onRetry});

  final KefeStrings strings;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(strings.perspectiveUnavailable),
        const SizedBox(height: 12),
        OutlinedButton(
          key: const ValueKey('perspective-retry'),
          onPressed: onRetry,
          child: Text(strings.perspectiveRetry),
        ),
      ],
    );
  }
}

class _LoadedState extends StatelessWidget {
  const _LoadedState({required this.state, required this.result});

  final PerspectiveUiState state;
  final PerspectiveResult? result;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final snapshot = result;
    if (snapshot == null) {
      return Text(strings.perspectiveUnavailable);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (state == PerspectiveUiState.degradedCurated) ...[
          Text(
            strings.perspectiveCuratedNote,
            key: const ValueKey('perspective-curated-note'),
          ),
          const SizedBox(height: 12),
        ],
        if (state == PerspectiveUiState.clusterPending) ...[
          Text(
            strings.perspectiveClusterPending,
            key: const ValueKey('perspective-cluster-pending'),
          ),
          const SizedBox(height: 12),
        ],
        if (snapshot.cards.isEmpty)
          Text(strings.perspectiveEmpty)
        else
          for (final card in snapshot.cards) ...[
            _PerspectiveCardView(card: card),
            const SizedBox(height: 12),
          ],
        ExpansionTile(
          key: const ValueKey('perspective-methodology'),
          tilePadding: EdgeInsets.zero,
          childrenPadding: const EdgeInsets.only(bottom: 8),
          title: Text(strings.perspectiveMethodology),
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Text(snapshot.methodology.provenanceNote),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                '${snapshot.methodology.sampleKind} · '
                'n=${snapshot.methodology.sampleSize}',
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _PerspectiveCardView extends StatelessWidget {
  const _PerspectiveCardView({required this.card});

  final PerspectiveCard card;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    return Container(
      key: ValueKey('perspective-card-${card.slot.name}'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            strings.perspectiveSlotLabel(card.slot),
            style: Theme.of(context).textTheme.labelLarge,
          ),
          const SizedBox(height: 8),
          Text(card.body),
          const SizedBox(height: 10),
          Text(
            '${strings.perspectiveSourceLabel(card.sourceKind)} · '
            '${card.provenanceLabel}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
