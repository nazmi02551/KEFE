import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_theme.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../community_reason/presentation/community_reason_section.dart';
import '../../consensus/presentation/consensus_section.dart';
import '../../progress/presentation/progress_section.dart';
import '../../sharing/presentation/share_section.dart';
import '../application/decision_controller.dart';
import '../domain/decision_models.dart';

class PerspectiveSection extends ConsumerWidget {
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
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final decision = ref.watch(decisionControllerProvider);
    final sessionId = decision.sessionId;
    final caseVersionId = decision.caseData?.versionId;
    final hasCommittedContext =
        decision.reveal != null && sessionId != null && caseVersionId != null;
    final consensus = hasCommittedContext
        ? ConsensusSection(sessionId: sessionId, caseVersionId: caseVersionId)
        : null;
    final community = hasCommittedContext
        ? CommunityReasonSection(
            sessionId: sessionId,
            caseVersionId: caseVersionId,
          )
        : null;
    final share = hasCommittedContext
        ? ShareSection(sessionId: sessionId)
        : null;

    if (state == PerspectiveUiState.idle) {
      if (!hasCommittedContext) return const SizedBox.shrink();
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ?consensus,
          if (community != null) ...[const SizedBox(height: 20), community],
          if (share != null) ...[const SizedBox(height: 20), share],
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          key: const ValueKey('perspective-section'),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: const Color(0xFF8E7CFF).withValues(alpha: 0.11),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.forum_outlined,
                        color: Color(0xFFAA9CFF),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'KARŞI GÖRÜŞLER',
                            style: Theme.of(context).textTheme.labelSmall
                                ?.copyWith(
                                  color: const Color(0xFFAA9CFF),
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: 0.8,
                                ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            strings.perspectiveTitle,
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ],
                      ),
                    ),
                  ],
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
                const SizedBox(height: 14),
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
        ),
        if (consensus != null) ...[const SizedBox(height: 20), consensus],
        if (community != null) ...[const SizedBox(height: 20), community],
        const SizedBox(height: 20),
        const ProgressSection(),
        if (share != null) ...[const SizedBox(height: 20), share],
      ],
    );
  }
}

class _LoadingState extends StatelessWidget {
  const _LoadingState({required this.strings});
  final KefeStrings strings;

  @override
  Widget build(BuildContext context) => Semantics(
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

class _RetryState extends StatelessWidget {
  const _RetryState({required this.strings, required this.onRetry});
  final KefeStrings strings;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Column(
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

class _LoadedState extends StatelessWidget {
  const _LoadedState({required this.state, required this.result});
  final PerspectiveUiState state;
  final PerspectiveResult? result;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final snapshot = result;
    if (snapshot == null) return Text(strings.perspectiveUnavailable);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (state == PerspectiveUiState.degradedCurated) ...[
          KeyedSubtree(
            key: const ValueKey('perspective-curated-note'),
            child: _MethodNote(
              icon: Icons.verified_outlined,
              text: strings.perspectiveCuratedNote,
            ),
          ),
          const SizedBox(height: 12),
        ],
        if (state == PerspectiveUiState.clusterPending) ...[
          KeyedSubtree(
            key: const ValueKey('perspective-cluster-pending'),
            child: _MethodNote(
              icon: Icons.hourglass_top_rounded,
              text: strings.perspectiveClusterPending,
            ),
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
        Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            key: const ValueKey('perspective-methodology'),
            tilePadding: const EdgeInsets.symmetric(horizontal: 2),
            childrenPadding: const EdgeInsets.only(bottom: 8),
            title: Text(
              strings.perspectiveMethodology,
              style: Theme.of(
                context,
              ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
            ),
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  snapshot.methodology.provenanceNote,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: KefeColorTokens.textMutedDark,
                    height: 1.4,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '${snapshot.methodology.sampleKind} · n=${snapshot.methodology.sampleSize}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: KefeColorTokens.goldSoft,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MethodNote extends StatelessWidget {
  const _MethodNote({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(11),
    decoration: BoxDecoration(
      color: KefeColorTokens.rules.withValues(alpha: 0.07),
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: KefeColorTokens.rules.withValues(alpha: 0.18)),
    ),
    child: Row(
      children: [
        Icon(icon, size: 17, color: KefeColorTokens.rules),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: KefeColorTokens.textMutedDark,
            ),
          ),
        ),
      ],
    ),
  );
}

class _PerspectiveCardView extends StatelessWidget {
  const _PerspectiveCardView({required this.card});
  final PerspectiveCard card;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = _slotVisual(card.slot);
    return Container(
      key: ValueKey('perspective-card-${card.slot.name}'),
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: visual.color.withValues(alpha: 0.055),
        border: Border.all(color: visual.color.withValues(alpha: 0.26)),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: visual.color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(9),
                ),
                child: Icon(visual.icon, size: 16, color: visual.color),
              ),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  strings.perspectiveSlotLabel(card.slot),
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: visual.color,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 11),
          Text(
            card.body,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(height: 1.45),
          ),
          const SizedBox(height: 11),
          Text(
            '${strings.perspectiveSourceLabel(card.sourceKind)} · ${card.provenanceLabel}',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: KefeColorTokens.textMutedDark,
            ),
          ),
        ],
      ),
    );
  }
}

({Color color, IconData icon}) _slotVisual(PerspectiveSlot slot) =>
    switch (slot) {
      PerspectiveSlot.near => (
        color: KefeColorTokens.success,
        icon: Icons.thumb_up_alt_outlined,
      ),
      PerspectiveSlot.opposing => (
        color: KefeColorTokens.empathy,
        icon: Icons.swap_horiz_rounded,
      ),
      PerspectiveSlot.bridge => (
        color: const Color(0xFFAA9CFF),
        icon: Icons.hub_outlined,
      ),
      PerspectiveSlot.alternativeContext => (
        color: KefeColorTokens.rules,
        icon: Icons.change_circle_outlined,
      ),
    };
