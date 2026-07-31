import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../application/consensus_controller.dart';
import '../domain/consensus_models.dart';

class ConsensusSection extends ConsumerStatefulWidget {
  const ConsensusSection({
    required this.sessionId,
    required this.caseVersionId,
    super.key,
  });

  final String sessionId;
  final String caseVersionId;

  @override
  ConsumerState<ConsensusSection> createState() => _ConsensusSectionState();
}

class _ConsensusSectionState extends ConsumerState<ConsensusSection> {
  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  @override
  void didUpdateWidget(covariant ConsensusSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sessionId != widget.sessionId ||
        oldWidget.caseVersionId != widget.caseVersionId) {
      Future.microtask(() => _load(force: true));
    }
  }

  Future<void> _load({bool force = false}) => ref
      .read(consensusControllerProvider.notifier)
      .load(
        sessionId: widget.sessionId,
        caseVersionId: widget.caseVersionId,
        force: force,
      );

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(consensusControllerProvider);
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    if (state.sessionId != null && state.sessionId != widget.sessionId) {
      return const SizedBox.shrink();
    }
    switch (state.uiState) {
      case ConsensusUiState.idle:
      case ConsensusUiState.loading:
        return _ConsensusFrame(
          child: Semantics(
            liveRegion: true,
            label: strings.consensusLoading,
            child: _StatusNotice(
              icon: Icons.hourglass_empty_rounded,
              title: strings.consensusLoading,
              accent: visual.rules,
            ),
          ),
        );
      case ConsensusUiState.empty:
        return const SizedBox.shrink();
      case ConsensusUiState.blocked:
        return _ConsensusFrame(
          child: _Notice(
            icon: Icons.lock_outline_rounded,
            title: strings.consensusCommitFirst,
            body: strings.consensusCommitFirstBody,
          ),
        );
      case ConsensusUiState.errorRetryable:
        return _ConsensusFrame(
          child: _ErrorState(
            message: strings.consensusUnavailable(state.errorCode),
            retryLabel: strings.consensusRetry,
            onRetry: ref.read(consensusControllerProvider.notifier).retry,
          ),
        );
      case ConsensusUiState.eligible:
      case ConsensusUiState.submitting:
      case ConsensusUiState.participated:
        if (state.cards.isEmpty) return const SizedBox.shrink();
        final active = state.activeCard;
        final completed = state.cards
            .where((card) => card.participated)
            .toList();
        return Column(
          key: const ValueKey('consensus-section'),
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (final card in completed) ...[
              _ConsensusCardResult(card: card),
              const SizedBox(height: 14),
            ],
            if (active != null && !active.participated)
              _ConsensusParticipationCard(
                card: active,
                state: state,
                submitting: state.uiState == ConsensusUiState.submitting,
              ),
          ],
        );
    }
  }
}

class _ConsensusParticipationCard extends ConsumerWidget {
  const _ConsensusParticipationCard({
    required this.card,
    required this.state,
    required this.submitting,
  });

  final ConsensusCard card;
  final ConsensusState state;
  final bool submitting;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = KefeStrings.of(context);
    final controller = ref.read(consensusControllerProvider.notifier);
    final visual = context.kefeVisual;
    return _ConsensusFrame(
      key: ValueKey('consensus-card-${card.versionId}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _ConsensusHeader(),
          const SizedBox(height: 14),
          _IntegrityBadge(text: strings.consensusExposed),
          const SizedBox(height: 16),
          Text(
            card.proposition,
            key: const ValueKey('consensus-proposition'),
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w900,
              height: 1.22,
            ),
          ),
          const SizedBox(height: 9),
          Text(
            strings.consensusPrompt,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: visual.mutedForeground,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 18),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final stance in card.stanceCodes)
                ChoiceChip(
                  key: ValueKey('consensus-stance-$stance'),
                  label: Text(strings.consensusStanceLabel(stance)),
                  selected: state.selectedStance == stance,
                  onSelected: submitting
                      ? null
                      : (_) => controller.selectStance(stance),
                ),
            ],
          ),
          if (card.reasonTagCodes.isNotEmpty) ...[
            const SizedBox(height: 18),
            Text(
              strings.consensusReasonLimit(card.maxReasonTags),
              style: Theme.of(
                context,
              ).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 9),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final tag in card.reasonTagCodes)
                  FilterChip(
                    key: ValueKey('consensus-reason-$tag'),
                    label: Text(strings.consensusReasonLabel(tag)),
                    selected: state.selectedReasonTags.contains(tag),
                    onSelected: submitting
                        ? null
                        : (_) => controller.toggleReasonTag(tag),
                  ),
              ],
            ),
          ],
          const SizedBox(height: 20),
          FilledButton.icon(
            key: const ValueKey('consensus-submit'),
            onPressed: state.canSubmit && !submitting
                ? controller.submit
                : null,
            icon: Icon(
              submitting
                  ? Icons.hourglass_top_rounded
                  : Icons.how_to_vote_outlined,
            ),
            label: Text(
              submitting ? strings.consensusSubmitting : strings.consensusJoin,
            ),
          ),
          const SizedBox(height: 12),
          _MethodNote(text: strings.consensusExposedMethodology),
        ],
      ),
    );
  }
}

class _ConsensusCardResult extends StatelessWidget {
  const _ConsensusCardResult({required this.card});

  final ConsensusCard card;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final aggregate = card.aggregate!;
    return _ConsensusFrame(
      key: ValueKey('consensus-result-${card.versionId}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _ConsensusHeader(),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              _IntegrityBadge(
                text:
                    '${aggregate.contributionClass} · n=${aggregate.sampleSize}',
              ),
              Icon(
                Icons.check_circle_rounded,
                color: visual.success,
                semanticLabel: strings.consensusDistribution,
              ),
            ],
          ),
          const SizedBox(height: 15),
          Text(
            card.proposition,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w900,
              height: 1.25,
            ),
          ),
          const SizedBox(height: 18),
          KefeEyebrow(strings.consensusDistribution, color: visual.goldSoft),
          const SizedBox(height: 12),
          for (final stance in card.stanceCodes) ...[
            _DistributionRow(
              label: strings.consensusStanceLabel(stance),
              value: aggregate.stanceDistribution[stance] ?? 0,
              selected: card.participation?.stanceCode == stance,
            ),
            const SizedBox(height: 11),
          ],
          if (aggregate.reasonPatternDistribution.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              strings.consensusReasonPatterns,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: visual.mutedForeground,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.7,
              ),
            ),
            const SizedBox(height: 9),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: aggregate.reasonPatternDistribution.entries
                  .map(
                    (entry) => _ResultChip(
                      label:
                          '${strings.consensusReasonLabel(entry.key)} · %${(entry.value * 100).round()}',
                    ),
                  )
                  .toList(growable: false),
            ),
          ],
          const SizedBox(height: 15),
          _MethodNote(
            key: const ValueKey('consensus-methodology-note'),
            text: aggregate.provenanceNote,
          ),
        ],
      ),
    );
  }
}

class _ConsensusFrame extends StatelessWidget {
  const _ConsensusFrame({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.raised,
      accent: visual.gold,
      padding: const EdgeInsets.all(18),
      child: child,
    );
  }
}

class _ConsensusHeader extends StatelessWidget {
  const _ConsensusHeader();

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: visual.subtleGoldSurface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: visual.gold.withValues(alpha: 0.24)),
          ),
          child: Icon(Icons.hub_outlined, color: visual.goldSoft),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              KefeEyebrow(strings.consensusEyebrow, color: visual.goldSoft),
              const SizedBox(height: 3),
              Text(
                strings.consensusCardTitle,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w900,
                  height: 1.15,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _IntegrityBadge extends StatelessWidget {
  const _IntegrityBadge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: visual.subtleRulesSurface,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: visual.rules.withValues(alpha: 0.24)),
      ),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: visual.rules,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _DistributionRow extends StatelessWidget {
  const _DistributionRow({
    required this.label,
    required this.value,
    required this.selected,
  });

  final String label;
  final double value;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final normalized = value.clamp(0, 1).toDouble();
    final accent = selected ? visual.gold : visual.rules;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: selected ? FontWeight.w900 : FontWeight.w600,
                ),
              ),
            ),
            Text(
              '%${(normalized * 100).round()}',
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                color: selected ? visual.goldSoft : visual.mutedForeground,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
        const SizedBox(height: 7),
        ClipRRect(
          borderRadius: BorderRadius.circular(999),
          child: LinearProgressIndicator(
            value: normalized,
            minHeight: 8,
            backgroundColor: visual.surfaceSunken,
            color: accent,
          ),
        ),
      ],
    );
  }
}

class _ResultChip extends StatelessWidget {
  const _ResultChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: visual.surfaceSunken,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: visual.border),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: visual.mutedForeground,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _MethodNote extends StatelessWidget {
  const _MethodNote({required this.text, super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.sunken,
      accent: visual.rules,
      padding: const EdgeInsets.all(13),
      borderRadius: 16,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.science_outlined, size: 19, color: visual.rules),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: visual.mutedForeground,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusNotice extends StatelessWidget {
  const _StatusNotice({
    required this.icon,
    required this.title,
    required this.accent,
  });

  final IconData icon;
  final String title;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.sunken,
      accent: accent,
      padding: const EdgeInsets.all(13),
      borderRadius: 16,
      child: Row(
        children: [
          Icon(icon, color: accent),
          const SizedBox(width: 11),
          Expanded(
            child: Text(
              title,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: visual.mutedForeground,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.icon, required this.title, required this.body});

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.sunken,
      accent: visual.attention,
      padding: const EdgeInsets.all(13),
      borderRadius: 16,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: visual.attention),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  body,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.mutedForeground,
                    height: 1.4,
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

class _ErrorState extends StatelessWidget {
  const _ErrorState({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
  });

  final String message;
  final String retryLabel;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return KefeSurface(
      tone: KefeSurfaceTone.sunken,
      accent: visual.attention,
      padding: const EdgeInsets.all(13),
      borderRadius: 16,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.info_outline_rounded, color: visual.attention),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  message,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: visual.mutedForeground,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: Text(retryLabel),
          ),
        ],
      ),
    );
  }
}
